from pathlib import Path
import json
import pandas as pd


class ReportBuilder:
    def __init__(self, output_dir: str | Path = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _parse_json(self, value):
        if value is None:
            return None

        if isinstance(value, (dict, list)):
            return value

        if isinstance(value, float) and pd.isna(value):
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

            if value.startswith("{") or value.startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return None

        return None

    def _safe(self, value, default=""):
        if value is None:
            return default

        if isinstance(value, float) and pd.isna(value):
            return default

        return value

    def _row_get(self, row, key: str, default=""):
        if key not in row:
            return default

        return self._safe(row[key], default)

    def _evidence_from_row(self, row) -> dict:
        evidence = self._row_get(row, "evidence_hit", None)
        parsed = self._parse_json(evidence)

        if isinstance(parsed, dict):
            return parsed

        # If the dataframe is already flat EvidenceHit rows
        return row.to_dict()

    def _record_ref_from_evidence(self, evidence: dict) -> dict:
        record_ref = evidence.get("record_ref")
        parsed = self._parse_json(record_ref)

        if isinstance(parsed, dict):
            return parsed

        if isinstance(record_ref, dict):
            return record_ref

        return {}

    def _score_components_text(self, row) -> list[str]:
        raw = self._row_get(row, "score_components", None)
        components = self._parse_json(raw)

        if not isinstance(components, list):
            return []

        lines = []

        for component in components:
            if not isinstance(component, dict):
                continue

            name = component.get("name", "")
            value = component.get("value", "")
            reason = component.get("reason", "")

            lines.append(f"  - {name}: {value} — {reason}")

        return lines

    def build_markdown(
        self,
        df: pd.DataFrame,
        name: str = "latest_watchlist_report.md",
    ) -> Path:
        path = self.output_dir / name

        lines = ["# Watchlist Report", ""]

        if df.empty:
            lines.append("No evidence hits found.")
            path.write_text("\n".join(lines), encoding="utf-8")
            return path

        df = df.copy()

        if "total_score" in df.columns:
            df["_sort_score"] = pd.to_numeric(df["total_score"], errors="coerce").fillna(0)
        elif "relevance_score" in df.columns:
            df["_sort_score"] = pd.to_numeric(df["relevance_score"], errors="coerce").fillna(0)
        else:
            df["_sort_score"] = 0

        if "relevance_label" in df.columns:
            high_hits = df[df["relevance_label"].isin(["high", "critical"])]
        else:
            high_hits = pd.DataFrame()

        lines.append(f"Total hits: {len(df)}")
        lines.append(f"High/Critical hits: {len(high_hits)}")
        lines.append("")

        df = df.sort_values("_sort_score", ascending=False)

        for _, row in df.iterrows():
            evidence = self._evidence_from_row(row)
            record_ref = self._record_ref_from_evidence(evidence)

            label = self._row_get(row, "relevance_label", "unlabeled")
            total_score = self._row_get(row, "total_score", "")
            relevance_score = self._row_get(row, "relevance_score", "")
            routing_decision = self._row_get(row, "routing_decision", "")

            entity_name = (
                evidence.get("subject_entity_name")
                or evidence.get("subject_entity_id")
                or "Context hit"
            )

            source = (
                record_ref.get("source")
                or evidence.get("source")
                or "unknown"
            )

            dataset = (
                record_ref.get("dataset")
                or evidence.get("dataset")
                or ""
            )

            title = evidence.get("title") or "Untitled"
            description = evidence.get("description") or ""
            url = evidence.get("url") or ""
            published_at = evidence.get("published_at") or evidence.get("occurred_at") or ""
            hit_scope = evidence.get("hit_scope") or ""
            concepts = evidence.get("matched_concept_ids") or []
            context_keys = evidence.get("context_keys") or []

            lines.append(f"## {entity_name} — {str(label).upper()}")
            lines.append(f"- Source: {source}")
            if dataset:
                lines.append(f"- Dataset: {dataset}")
            lines.append(f"- Scope: {hit_scope}")
            lines.append(f"- Title: {title}")

            if description:
                lines.append(f"- Description: {description}")

            if total_score != "":
                lines.append(f"- Total Score: {total_score}")

            if relevance_score != "":
                lines.append(f"- Relevance Score: {relevance_score}")

            if routing_decision:
                lines.append(f"- Routing Decision: {routing_decision}")

            if concepts:
                lines.append(f"- Concepts: {concepts}")

            if context_keys:
                lines.append(f"- Context Keys: {context_keys}")

            if url:
                lines.append(f"- URL: {url}")

            if published_at:
                lines.append(f"- Date: {published_at}")

            component_lines = self._score_components_text(row)
            if component_lines:
                lines.append("- Score Breakdown:")
                lines.extend(component_lines)

            lines.append("")

        df = df.drop(columns=["_sort_score"], errors="ignore")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path