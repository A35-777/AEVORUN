"""AST-based feature extraction for Python source code.

Extracts structural, semantic, and temporal features from Python functions
safely, without requiring remote LLMs or runtime code execution.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import numpy as np


@dataclass
class CodeEvidence:
    """Evidence snippet explaining why a feature was triggered."""
    feature_name: str
    line_number: int
    snippet: str
    description: str


@dataclass
class ExtractedFeatures:
    """Container for extracted features and metadata from a Python function."""
    function_name: str
    is_valid_syntax: bool
    unsupported_reason: Optional[str]
    is_temporal: bool
    feature_dict: Dict[str, float]
    feature_vector: np.ndarray
    evidence: List[CodeEvidence] = field(default_factory=list)
    ast_hash: str = ""
    lines_of_code: int = 0


# Fixed feature vocabulary ordering (ensures deterministic feature vectors)
FEATURE_NAMES: List[str] = [
    # 1. Structural & Complexity (12)
    "num_ast_nodes",
    "num_lines",
    "max_depth",
    "num_args",
    "num_branches",
    "num_loops",
    "num_try_blocks",
    "num_calls",
    "num_attributes",
    "num_returns",
    "has_type_annotations",
    "has_docstring",

    # 2. Module & Library Imports (8)
    "import_datetime",
    "import_dateutil",
    "import_pytz",
    "import_zoneinfo",
    "import_time",
    "import_calendar",
    "import_arrow",
    "import_pandas",

    # 3. Core Temporal Calls & Methods (16)
    "call_datetime_now",
    "call_datetime_utcnow",
    "call_date_today",
    "call_astimezone",
    "call_replace",
    "call_replace_year",
    "call_replace_month",
    "call_replace_day",
    "call_replace_hour",
    "call_replace_tzinfo",
    "call_strptime",
    "call_strftime",
    "call_fromisoformat",
    "call_isoformat",
    "call_timestamp",
    "call_fromtimestamp",

    # 4. Arithmetic & Duration Calls (8)
    "call_timedelta",
    "call_relativedelta",
    "call_calendar_isleap",
    "call_monthrange",
    "call_weekday_or_iso",
    "call_zoneinfo",
    "call_time_time",
    "call_utcoffset",

    # 5. Timedelta / Function Arguments (10)
    "kwarg_days",
    "kwarg_seconds",
    "kwarg_microseconds",
    "kwarg_milliseconds",
    "kwarg_minutes",
    "kwarg_hours",
    "kwarg_weeks",
    "kwarg_months",
    "kwarg_years",
    "kwarg_fold",

    # 6. Numeric Constants in Temporal Context (10)
    "const_0",
    "const_1",
    "const_7",
    "const_12",
    "const_23_or_24",
    "const_28_to_31",
    "const_60",
    "const_365_or_366",
    "const_1000",
    "const_86400",

    # 7. Operators & Comparisons (6)
    "op_subtraction",
    "op_addition",
    "op_compare_lt_le",
    "op_compare_gt_ge",
    "op_compare_eq_ne",
    "op_modulo",

    # 8. Identifier Semantic Indicators (12)
    "name_expire_ttl_deadline",
    "name_schedule_cron_interval",
    "name_start_end_range",
    "name_utc_tz_zone_offset",
    "name_timestamp_epoch",
    "name_duration_delta_elapsed",
    "name_month_year_annual",
    "name_leap_feb",
    "name_midnight_night_day",
    "name_parse_format_iso",
    "name_now_today_time",
    "name_fold_dst_ambiguous",
]

FEATURE_DIM = len(FEATURE_NAMES)
FEATURE_INDEX_MAP = {name: idx for idx, name in enumerate(FEATURE_NAMES)}


class TemporalASTVisitor(ast.NodeVisitor):
    """AST Visitor that traverses a function AST and computes structural & temporal metrics."""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.node_count = 0
        self.max_depth = 0
        self.current_depth = 0
        self.num_args = 0
        self.num_branches = 0
        self.num_loops = 0
        self.num_try_blocks = 0
        self.num_calls = 0
        self.num_attributes = 0
        self.num_returns = 0
        self.has_type_annotations = 0.0
        self.has_docstring = 0.0

        # Imports
        self.imports = set()

        # Call sets
        self.calls = set()
        self.attributes = set()
        self.kwargs = set()
        self.constants = set()
        self.operators = set()
        self.identifiers = set()

        self.evidence: List[CodeEvidence] = []

    def _get_line_snippet(self, node: ast.AST) -> str:
        lineno = getattr(node, "lineno", 1)
        if 0 < lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def visit(self, node: ast.AST):
        self.node_count += 1
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth
        super().visit(node)
        self.current_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.num_args = len(node.args.args)
        if node.returns or any(arg.annotation for arg in node.args.args):
            self.has_type_annotations = 1.0
        if ast.get_docstring(node):
            self.has_docstring = 1.0
        self.identifiers.add(node.name.lower())
        for arg in node.args.args:
            self.identifiers.add(arg.arg.lower())
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.num_args = len(node.args.args)
        if node.returns or any(arg.annotation for arg in node.args.args):
            self.has_type_annotations = 1.0
        if ast.get_docstring(node):
            self.has_docstring = 1.0
        self.identifiers.add(node.name.lower())
        for arg in node.args.args:
            self.identifiers.add(arg.arg.lower())
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.num_branches += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.num_loops += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.num_loops += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self.num_try_blocks += 1
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        self.num_returns += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.name.lower()
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            mod = node.module.lower()
            self.imports.add(mod)
        for alias in node.names:
            self.imports.add(alias.name.lower())
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        self.num_calls += 1
        # Extract function call name
        call_name = ""
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            call_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                call_name = f"{node.func.value.id}.{node.func.attr}"

        call_name_lower = call_name.lower()
        self.calls.add(call_name_lower)

        # Inspect keyword arguments
        for kw in node.keywords:
            if kw.arg:
                kw_lower = kw.arg.lower()
                self.kwargs.add(kw_lower)
                if kw_lower == "year" and "replace" in call_name_lower:
                    self.calls.add("call_replace_year")
                    self.evidence.append(CodeEvidence(
                        "call_replace_year", getattr(node, "lineno", 1),
                        self._get_line_snippet(node), "Explicit year replacement (leap day sensitivity)"
                    ))
                elif kw_lower == "month" and "replace" in call_name_lower:
                    self.calls.add("call_replace_month")
                    self.evidence.append(CodeEvidence(
                        "call_replace_month", getattr(node, "lineno", 1),
                        self._get_line_snippet(node), "Explicit month replacement (month end boundary sensitivity)"
                    ))
                elif kw_lower == "day" and "replace" in call_name_lower:
                    self.calls.add("call_replace_day")
                elif kw_lower == "hour" and "replace" in call_name_lower:
                    self.calls.add("call_replace_hour")
                elif kw_lower == "tzinfo" and "replace" in call_name_lower:
                    self.calls.add("call_replace_tzinfo")
                    self.evidence.append(CodeEvidence(
                        "call_replace_tzinfo", getattr(node, "lineno", 1),
                        self._get_line_snippet(node), "Direct tzinfo replacement instead of proper astimezone conversion"
                    ))

        # Check for specific temporal calls
        if "now" in call_name_lower:
            self.calls.add("call_datetime_now")
            self.evidence.append(CodeEvidence(
                "call_datetime_now", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Current local/naive time retrieval"
            ))
        if "utcnow" in call_name_lower:
            self.calls.add("call_datetime_utcnow")
            self.evidence.append(CodeEvidence(
                "call_datetime_utcnow", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Deprecated naive UTC time retrieval"
            ))
        if "today" in call_name_lower:
            self.calls.add("call_date_today")
        if "astimezone" in call_name_lower:
            self.calls.add("call_astimezone")
            self.evidence.append(CodeEvidence(
                "call_astimezone", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Timezone offset conversion"
            ))
        if "replace" in call_name_lower:
            self.calls.add("call_replace")
        if "strptime" in call_name_lower:
            self.calls.add("call_strptime")
            self.evidence.append(CodeEvidence(
                "call_strptime", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Custom format string date parsing"
            ))
        if "strftime" in call_name_lower:
            self.calls.add("call_strftime")
        if "fromisoformat" in call_name_lower:
            self.calls.add("call_fromisoformat")
            self.evidence.append(CodeEvidence(
                "call_fromisoformat", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "ISO 8601 string parsing"
            ))
        if "isoformat" in call_name_lower:
            self.calls.add("call_isoformat")
        if "fromtimestamp" in call_name_lower:
            self.calls.add("call_fromtimestamp")
        elif "timestamp" in call_name_lower:
            self.calls.add("call_timestamp")
        if "timedelta" in call_name_lower:
            self.calls.add("call_timedelta")
            self.evidence.append(CodeEvidence(
                "call_timedelta", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Fixed physical duration arithmetic"
            ))
        if "relativedelta" in call_name_lower:
            self.calls.add("call_relativedelta")
            self.evidence.append(CodeEvidence(
                "call_relativedelta", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Calendar-aware relative duration arithmetic"
            ))
        if "isleap" in call_name_lower:
            self.calls.add("call_calendar_isleap")
            self.evidence.append(CodeEvidence(
                "call_calendar_isleap", getattr(node, "lineno", 1),
                self._get_line_snippet(node), "Explicit leap year check"
            ))
        if "monthrange" in call_name_lower:
            self.calls.add("call_monthrange")
        if "weekday" in call_name_lower or "isoweekday" in call_name_lower:
            self.calls.add("call_weekday_or_iso")
        if "zoneinfo" in call_name_lower:
            self.calls.add("call_zoneinfo")
        if "time" in call_name_lower and ("time.time" in call_name_lower or call_name_lower == "time"):
            self.calls.add("call_time_time")
        if "utcoffset" in call_name_lower:
            self.calls.add("call_utcoffset")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.num_attributes += 1
        attr_lower = node.attr.lower()
        self.attributes.add(attr_lower)
        self.identifiers.add(attr_lower)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        self.identifiers.add(node.id.lower())
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            val = node.value
            if val == 0:
                self.constants.add("const_0")
            elif val == 1:
                self.constants.add("const_1")
            elif val == 7:
                self.constants.add("const_7")
            elif val == 12:
                self.constants.add("const_12")
            elif val in (23, 24):
                self.constants.add("const_23_or_24")
            elif val in (28, 29, 30, 31):
                self.constants.add("const_28_to_31")
            elif val == 60:
                self.constants.add("const_60")
            elif val in (365, 366):
                self.constants.add("const_365_or_366")
                self.evidence.append(CodeEvidence(
                    "const_365_or_366", getattr(node, "lineno", 1),
                    self._get_line_snippet(node), f"Hardcoded day count constant ({val})"
                ))
            elif val in (1000, 1000000):
                self.constants.add("const_1000")
            elif val == 86400:
                self.constants.add("const_86400")
        elif isinstance(node.value, str):
            val_lower = node.value.lower()
            if "utc" in val_lower or "gmt" in val_lower:
                self.identifiers.add("utc")
            if any(tz in val_lower for tz in ("america/", "europe/", "asia/", "pacific/")):
                self.identifiers.add("tz")
                self.evidence.append(CodeEvidence(
                    "tz_identifier", getattr(node, "lineno", 1),
                    self._get_line_snippet(node), f"Named IANA timezone string ({node.value})"
                ))
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, ast.Sub):
            self.operators.add("op_subtraction")
        elif isinstance(node.op, ast.Add):
            self.operators.add("op_addition")
        elif isinstance(node.op, ast.Mod):
            self.operators.add("op_modulo")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        for op in node.ops:
            if isinstance(op, (ast.Lt, ast.LtE)):
                self.operators.add("op_compare_lt_le")
            elif isinstance(op, (ast.Gt, ast.GtE)):
                self.operators.add("op_compare_gt_ge")
            elif isinstance(op, (ast.Eq, ast.NotEq)):
                self.operators.add("op_compare_eq_ne")
        self.generic_visit(node)


def extract_features_from_ast(
    func_node: ast.AST,
    source_lines: List[str],
    global_imports: Optional[Set[str]] = None,
    function_name: str = "unknown"
) -> ExtractedFeatures:
    """Extract features from a FunctionDef AST node."""
    visitor = TemporalASTVisitor(source_lines)
    if global_imports:
        visitor.imports.update(global_imports)
    visitor.visit(func_node)

    feat_dict: Dict[str, float] = {name: 0.0 for name in FEATURE_NAMES}

    # 1. Structural features (normalized)
    feat_dict["num_ast_nodes"] = min(visitor.node_count / 100.0, 1.0)
    feat_dict["num_lines"] = min(len(source_lines) / 100.0, 1.0)
    feat_dict["max_depth"] = min(visitor.max_depth / 20.0, 1.0)
    feat_dict["num_args"] = min(visitor.num_args / 10.0, 1.0)
    feat_dict["num_branches"] = min(visitor.num_branches / 10.0, 1.0)
    feat_dict["num_loops"] = min(visitor.num_loops / 5.0, 1.0)
    feat_dict["num_try_blocks"] = min(visitor.num_try_blocks / 5.0, 1.0)
    feat_dict["num_calls"] = min(visitor.num_calls / 20.0, 1.0)
    feat_dict["num_attributes"] = min(visitor.num_attributes / 20.0, 1.0)
    feat_dict["num_returns"] = min(visitor.num_returns / 5.0, 1.0)
    feat_dict["has_type_annotations"] = visitor.has_type_annotations
    feat_dict["has_docstring"] = visitor.has_docstring

    # 2. Imports
    for imp in visitor.imports:
        if "datetime" in imp:
            feat_dict["import_datetime"] = 1.0
        if "dateutil" in imp:
            feat_dict["import_dateutil"] = 1.0
        if "pytz" in imp:
            feat_dict["import_pytz"] = 1.0
        if "zoneinfo" in imp:
            feat_dict["import_zoneinfo"] = 1.0
        if "time" in imp:
            feat_dict["import_time"] = 1.0
        if "calendar" in imp:
            feat_dict["import_calendar"] = 1.0
        if "arrow" in imp:
            feat_dict["import_arrow"] = 1.0
        if "pandas" in imp:
            feat_dict["import_pandas"] = 1.0

    # 3. Core Temporal Calls
    for call in visitor.calls:
        if call in feat_dict:
            feat_dict[call] = 1.0
        if "replace" in call:
            feat_dict["call_replace"] = 1.0

    # 4. Arithmetic & Duration Calls
    for call in visitor.calls:
        if call in feat_dict:
            feat_dict[call] = 1.0

    # 5. Kwargs
    for kw in visitor.kwargs:
        kw_key = f"kwarg_{kw}"
        if kw_key in feat_dict:
            feat_dict[kw_key] = 1.0

    # 6. Constants
    for c in visitor.constants:
        if c in feat_dict:
            feat_dict[c] = 1.0

    # 7. Operators
    for op in visitor.operators:
        if op in feat_dict:
            feat_dict[op] = 1.0

    # 8. Identifier Semantics
    all_idents = " ".join(visitor.identifiers)
    if any(k in all_idents for k in ("expire", "ttl", "deadline", "valid", "timeout")):
        feat_dict["name_expire_ttl_deadline"] = 1.0
    if any(k in all_idents for k in ("schedule", "cron", "interval", "recur", "cadence", "step")):
        feat_dict["name_schedule_cron_interval"] = 1.0
    if any(k in all_idents for k in ("start", "end", "range", "from_date", "to_date", "until")):
        feat_dict["name_start_end_range"] = 1.0
    if any(k in all_idents for k in ("utc", "tz", "zone", "offset", "timezone", "zoneinfo")):
        feat_dict["name_utc_tz_zone_offset"] = 1.0
    if any(k in all_idents for k in ("timestamp", "epoch", "stamp", "posix", "unix")):
        feat_dict["name_timestamp_epoch"] = 1.0
    if any(k in all_idents for k in ("duration", "delta", "elapsed", "period", "diff")):
        feat_dict["name_duration_delta_elapsed"] = 1.0
    if any(k in all_idents for k in ("month", "year", "annual", "quarterly", "monthly")):
        feat_dict["name_month_year_annual"] = 1.0
    if any(k in all_idents for k in ("leap", "feb", "bissextile", "february")):
        feat_dict["name_leap_feb"] = 1.0
    if any(k in all_idents for k in ("midnight", "night", "day", "eod", "bod", "today")):
        feat_dict["name_midnight_night_day"] = 1.0
    if any(k in all_idents for k in ("parse", "format", "iso", "rfc", "strp", "strf")):
        feat_dict["name_parse_format_iso"] = 1.0
    if any(k in all_idents for k in ("now", "today", "clock", "current")):
        feat_dict["name_now_today_time"] = 1.0
    if any(k in all_idents for k in ("fold", "dst", "ambiguous", "nonexistent", "wall")):
        feat_dict["name_fold_dst_ambiguous"] = 1.0

    # Build vector
    vector = np.array([feat_dict[k] for k in FEATURE_NAMES], dtype=np.float32)

    # Check whether the function exhibits genuine temporal characteristics
    temporal_calls = sum(feat_dict[k] for k in FEATURE_NAMES if k.startswith("call_"))
    temporal_kwargs = sum(feat_dict[k] for k in FEATURE_NAMES if k.startswith("kwarg_"))
    temporal_imports = sum(feat_dict[k] for k in FEATURE_NAMES if k.startswith("import_"))
    # Specific temporal identifiers (exclude generic range/start/end which appear in math/loops)
    temporal_idents = sum(
        feat_dict[k] for k in FEATURE_NAMES
        if k.startswith("name_") and k not in ("name_start_end_range",)
    )

    is_temporal = bool(
        temporal_calls > 0
        or temporal_kwargs > 0
        or temporal_imports > 0
        or (temporal_idents >= 2.0)
    )

    # AST hash for deduplication
    ast_dump = ast.dump(func_node, include_attributes=False)
    # Simple hash of dump
    import hashlib
    ast_hash = hashlib.sha256(ast_dump.encode("utf-8")).hexdigest()[:16]

    return ExtractedFeatures(
        function_name=function_name,
        is_valid_syntax=True,
        unsupported_reason=None,
        is_temporal=is_temporal,
        feature_dict=feat_dict,
        feature_vector=vector,
        evidence=visitor.evidence,
        ast_hash=ast_hash,
        lines_of_code=len(source_lines)
    )


def extract_function_features(
    source_code: str,
    target_function_name: Optional[str] = None
) -> List[ExtractedFeatures]:
    """Extract features from Python source code safely.

    Handles syntax errors, incomplete files, multiple functions, and global imports.
    """
    source_lines = source_code.splitlines()

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        # Graceful failure on syntax error
        dummy_vector = np.zeros(FEATURE_DIM, dtype=np.float32)
        return [
            ExtractedFeatures(
                function_name=target_function_name or "<syntax_error>",
                is_valid_syntax=False,
                unsupported_reason=f"SyntaxError on line {e.lineno}: {e.msg}",
                is_temporal=False,
                feature_dict={name: 0.0 for name in FEATURE_NAMES},
                feature_vector=dummy_vector,
                evidence=[],
                ast_hash="",
                lines_of_code=len(source_lines)
            )
        ]

    # Gather module-level imports
    global_imports: Set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                global_imports.add(alias.name.lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                global_imports.add(node.module.lower())
            for alias in node.names:
                global_imports.add(alias.name.lower())

    results: List[ExtractedFeatures] = []

    # Find functions
    functions: List[Tuple[str, ast.AST, List[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if target_function_name is None or node.name == target_function_name:
                start_line = getattr(node, "lineno", 1) - 1
                end_line = getattr(node, "end_lineno", len(source_lines))
                fn_lines = source_lines[start_line:end_line]
                functions.append((node.name, node, fn_lines))

    # If no functions found, treat the top-level script as a single anonymous function block
    if not functions:
        fn_feat = extract_features_from_ast(
            tree, source_lines, global_imports, function_name="<module>"
        )
        results.append(fn_feat)
        return results

    for fn_name, fn_node, fn_lines in functions:
        fn_feat = extract_features_from_ast(
            fn_node, fn_lines, global_imports, function_name=fn_name
        )
        results.append(fn_feat)

    return results
