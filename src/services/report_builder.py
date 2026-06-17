from pathlib import Path
import pandas as pd

class ReportBuilder:
    def __init__(self, output_dir: str | Path = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_markdown(self, df: pd.DataFrame, name: str = "latest_watchlist_report.md") -> Path:
        path = self.output_dir / name

        lines = ["# Watchlist Report", ""]

        if df.empty:
            lines.append("No evidence hits found.")
            path.write_text("\n".join(lines), encoding="utf-8")
            return path

        high = df[df["relevance_label"] == "high"]

        lines.append(f"Total hits: {len(df)}")
        lines.append(f"High relevance hits: {len(high)}")
        lines.append("")

        for _, row in df.sort_values(["relevance_score", "published_at"], ascending=False).iterrows():
            lines.append(f"## {row['entity_name']} — {row['relevance_label'].upper()}")
            lines.append(f"- Source: {row['source']}")
            lines.append(f"- Title: {row['title']}")
            lines.append(f"- Score: {row['relevance_score']}")
            lines.append(f"- Reason: {row['reason']}")
            lines.append(f"- URL: {row['url']}")
            lines.append(f"- Publication Date: {row['published_at']}")
            lines.append(f"- Authors: {row['authors']}")
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path