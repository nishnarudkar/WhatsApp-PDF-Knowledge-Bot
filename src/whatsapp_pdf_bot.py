import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from PyPDF2 import PdfReader

# --------- Optional color support (falls back gracefully if colorama missing) ---------
try:
    from colorama import init as colorama_init, Fore, Style

    colorama_init(autoreset=True)
except ImportError:  # fallback if colorama not installed
    class Dummy:
        def __getattr__(self, name):
            return ""

    Fore = Style = Dummy()  # type: ignore

INDEX_VERSION = 2  # bumped because we added fields


# --------- Subject auto-tagging configuration ---------
SUBJECT_KEYWORDS: Dict[str, List[str]] = {
    "Machine Learning": [
        "regression",
        "classification",
        "loss function",
        "gradient descent",
        "supervised",
        "unsupervised",
        "overfitting",
        "underfitting",
        "ml",
    ],
    "Neural Networks": [
        "neuron",
        "backpropagation",
        "activation function",
        "cnn",
        "rnn",
        "deep learning",
        "hidden layer",
        "perceptron",
        "neural network",
    ],
    "DBMS": [
        "sql",
        "normalization",
        "transaction",
        "primary key",
        "foreign key",
        "relational",
        "acid",
        "database",
    ],
    "Data Structures & Algorithms": [
        "time complexity",
        "space complexity",
        "linked list",
        "stack",
        "queue",
        "tree",
        "graph",
        "algorithm",
        "sorting",
        "searching",
    ],
    "Probability & Statistics": [
        "random variable",
        "distribution",
        "bayes",
        "expected value",
        "variance",
        "probability",
        "markov",
    ],
}


@dataclass
class Document:
    filename: str
    path: str
    modified: str
    size_bytes: int
    preview: str
    content: str  # lowercased
    subject: str
    content_hash: str  # hash of a sample of the content


# --------- Helpers ---------


def infer_subject(text: str) -> str:
    """
    Very simple rule-based subject classifier based on keyword counts.
    Returns the best subject name or 'Unknown'.
    """
    text_l = text.lower()
    best_subject = "Unknown"
    best_score = 0

    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = 0
        for kw in keywords:
            score += text_l.count(kw)
        if score > best_score:
            best_score = score
            best_subject = subject

    return best_subject


def compute_content_hash(text: str, max_chars: int = 2000) -> str:
    """
    Compute a SHA-256 hash of the first max_chars characters of the text.
    Used for duplicate detection (same/similar content with different filenames).
    """
    sample = text[:max_chars].encode("utf-8", errors="ignore")
    return hashlib.sha256(sample).hexdigest()


def extract_pdf_text(
    pdf_path: Path, max_pages: int = 3, max_chars: int = 4000
) -> str:
    """
    Extract text from the first `max_pages` of a PDF file.
    Text is truncated to `max_chars` characters to keep the index small.
    """
    text_chunks: List[str] = []
    try:
        reader = PdfReader(str(pdf_path))
        num_pages = min(len(reader.pages), max_pages)

        for i in range(num_pages):
            page = reader.pages[i]
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)

            if sum(len(t) for t in text_chunks) >= max_chars:
                break

    except Exception as e:
        print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} Failed to read {pdf_path}: {e}")
        return ""

    full_text = "\n".join(text_chunks)
    return full_text[:max_chars]


def build_index(folder: Path, index_path: Path, max_pages: int = 3) -> None:
    """
    Create or refresh the index.json file with metadata, subject tags,
    content hashes, and short previews for each PDF in the given folder (recursively).
    """
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Folder does not exist or is not a directory: {folder}")

    pdf_files = list(folder.rglob("*.pdf"))
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Found {len(pdf_files)} PDF files under {folder}")

    documents: List[Dict] = []

    for pdf in pdf_files:
        print(f"{Fore.CYAN}[INDEX]{Style.RESET_ALL} Processing {pdf}")
        text = extract_pdf_text(pdf, max_pages=max_pages)
        content_lower = text.lower()

        subject = infer_subject(content_lower)
        stat = pdf.stat()

        doc_info = Document(
            filename=pdf.name,
            path=str(pdf.resolve()),
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size_bytes=stat.st_size,
            preview=text[:500],
            content=content_lower,
            subject=subject,
            content_hash=compute_content_hash(content_lower),
        )

        documents.append(doc_info.__dict__)

    index_data = {
        "version": INDEX_VERSION,
        "indexed_at": datetime.utcnow().isoformat() + "Z",
        "root_folder": str(folder.resolve()),
        "num_documents": len(documents),
        "documents": documents,
    }

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"{Fore.GREEN}[DONE]{Style.RESET_ALL} Index written to {index_path}")
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Indexed {len(documents)} documents.")


def load_index(index_path: Path) -> dict:
    if not index_path.exists():
        raise FileNotFoundError(
            f"Index file not found at {index_path}. "
            f"Run the 'index' command first."
        )
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_documents(
    documents: List[Dict],
    query: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    min_size_kb: Optional[int] = None,
    max_size_kb: Optional[int] = None,
) -> List[Tuple[int, Dict]]:
    """
    Internal search function that returns a list of (score, doc) tuples.
    Used by both CLI search and interactive mode.
    """
    query = query.strip().lower()
    if not query:
        return []

    query_terms = [q for q in query.split() if q]

    since_date: Optional[date] = None
    until_date: Optional[date] = None
    if since:
        since_date = date.fromisoformat(since)
    if until:
        until_date = date.fromisoformat(until)

    min_bytes = min_size_kb * 1024 if min_size_kb is not None else None
    max_bytes = max_size_kb * 1024 if max_size_kb is not None else None

    scored_docs: List[Tuple[int, Dict]] = []

    for doc in documents:
        # Date filter
        try:
            mod_dt = datetime.fromisoformat(doc["modified"]).date()
        except Exception:
            mod_dt = None

        if since_date and mod_dt and mod_dt < since_date:
            continue
        if until_date and mod_dt and mod_dt > until_date:
            continue

        # Size filter
        size_bytes = doc.get("size_bytes", 0)
        if min_bytes is not None and size_bytes < min_bytes:
            continue
        if max_bytes is not None and size_bytes > max_bytes:
            continue

        content = doc.get("content", "")
        score = 0
        for term in query_terms:
            score += content.count(term)
        if score > 0:
            scored_docs.append((score, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return scored_docs


def build_snippet(content: str, query_terms: List[str], max_length: int = 220) -> str:
    """
    Build a small snippet of text around the first occurrence of any query term.
    """
    first_pos = None
    first_term = None

    for term in query_terms:
        pos = content.find(term)
        if pos != -1 and (first_pos is None or pos < first_pos):
            first_pos = pos
            first_term = term

    if first_pos is None:
        return ""

    start = max(0, first_pos - max_length // 2)
    end = min(len(content), start + max_length)
    snippet = content[start:end].replace("\n", " ")

    for term in query_terms:
        snippet = snippet.replace(term, f"[{term}]", 1)

    return snippet + ("..." if end < len(content) else "")


def export_results(
    scored_docs: List[Tuple[int, Dict]], export_path: Path
) -> None:
    """
    Export search results to CSV or TXT based on file extension.
    """
    export_path.parent.mkdir(parents=True, exist_ok=True)
    ext = export_path.suffix.lower()

    if ext == ".csv":
        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "score",
                    "filename",
                    "path",
                    "subject",
                    "modified",
                    "size_kb",
                ]
            )
            for score, doc in scored_docs:
                writer.writerow(
                    [
                        score,
                        doc["filename"],
                        doc["path"],
                        doc.get("subject", "Unknown"),
                        doc["modified"],
                        f"{doc['size_bytes'] / 1024:.1f}",
                    ]
                )
    else:  # plain text export
        with open(export_path, "w", encoding="utf-8") as f:
            for rank, (score, doc) in enumerate(scored_docs, start=1):
                f.write(f"#{rank} (score: {score})\n")
                f.write(f"File    : {doc['filename']}\n")
                f.write(f"Path    : {doc['path']}\n")
                f.write(f"Subject : {doc.get('subject', 'Unknown')}\n")
                f.write(f"Modified: {doc['modified']}\n")
                f.write(f"Size    : {doc['size_bytes'] / 1024:.1f} KB\n")
                f.write("\n")
    print(f"{Fore.GREEN}[EXPORT]{Style.RESET_ALL} Results saved to {export_path}")


def search_index(
    index_path: Path,
    query: str,
    top_k: int = 5,
    since: Optional[str] = None,
    until: Optional[str] = None,
    min_size_kb: Optional[int] = None,
    max_size_kb: Optional[int] = None,
    export: Optional[Path] = None,
) -> None:
    index_data = load_index(index_path)
    documents = index_data.get("documents", [])

    try:
        scored_docs = search_documents(
            documents, query, since, until, min_size_kb, max_size_kb
        )
    except ValueError:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Invalid date format. Use YYYY-MM-DD.")
        return

    if not scored_docs:
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} No matches found for given filters.")
        return

    query_terms = [q for q in query.strip().lower().split() if q]

    print(
        f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Found {len(scored_docs)} matching documents. "
        f"Showing top {top_k}:\n"
    )

    for rank, (score, doc) in enumerate(scored_docs[:top_k], start=1):
        print(f"{Fore.GREEN}#{rank}{Style.RESET_ALL}  (score: {score})")
        print(f"{Fore.CYAN}File    :{Style.RESET_ALL} {doc['filename']}")
        print(f"{Fore.CYAN}Path    :{Style.RESET_ALL} {doc['path']}")
        print(f"{Fore.CYAN}Subject :{Style.RESET_ALL} {doc.get('subject', 'Unknown')}")
        print(f"{Fore.CYAN}Modified:{Style.RESET_ALL} {doc['modified']}")
        print(f"{Fore.CYAN}Size    :{Style.RESET_ALL} {doc['size_bytes'] / 1024:.1f} KB")

        snippet = build_snippet(doc["content"], query_terms, max_length=220)
        if snippet:
            print(f"{Fore.MAGENTA}Snippet :{Style.RESET_ALL} {snippet}")
        else:
            print("Snippet : (no snippet available)")
        print("-" * 80)

    if export:
        export_results(scored_docs[:top_k], export)


def find_duplicates(index_path: Path, min_group_size: int = 2) -> None:
    """
    Detect duplicate PDFs based on content hash and show groups of similar files.
    """
    index_data = load_index(index_path)
    docs = index_data.get("documents", [])

    if not docs:
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Index is empty.")
        return

    groups: Dict[str, List[Dict]] = defaultdict(list)
    for d in docs:
        h = d.get("content_hash", "")
        if not h:
            continue
        groups[h].append(d)

    dup_groups = [g for g in groups.values() if len(g) >= min_group_size]

    if not dup_groups:
        print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} No duplicate PDFs detected based on content.")
        return

    print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Found {len(dup_groups)} duplicate groups:\n")

    for i, group in enumerate(dup_groups, start=1):
        print(f"{Fore.MAGENTA}Group #{i}{Style.RESET_ALL} (size: {len(group)})")
        for doc in group:
            print(f"- {doc['filename']}  ({doc['path']})")
        print("-" * 80)


def show_stats(index_path: Path) -> None:
    """
    Show high-level insights about the indexed PDFs:
    - Count, total size, avg size
    - Oldest and newest modification times
    - Top folders
    - Subject distribution
    - Top frequent words
    """
    index_data = load_index(index_path)
    docs = index_data.get("documents", [])

    if not docs:
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Index is empty.")
        return

    num_docs = len(docs)
    total_bytes = sum(d.get("size_bytes", 0) for d in docs)
    avg_bytes = total_bytes / num_docs

    valid_dates: List[datetime] = []
    for d in docs:
        try:
            valid_dates.append(datetime.fromisoformat(d["modified"]))
        except Exception:
            continue

    oldest = min(valid_dates) if valid_dates else None
    newest = max(valid_dates) if valid_dates else None

    folder_counts = Counter()
    subject_counts = Counter()
    for d in docs:
        folder = str(Path(d["path"]).parent)
        folder_counts[folder] += 1
        subject_counts[d.get("subject", "Unknown")] += 1

    stopwords = {
        "the",
        "and",
        "of",
        "to",
        "a",
        "in",
        "is",
        "for",
        "on",
        "that",
        "this",
        "with",
        "as",
        "are",
        "at",
        "by",
        "an",
        "be",
        "or",
        "from",
        "it",
        "we",
        "you",
        "not",
    }
    word_counts = Counter()
    for d in docs:
        text = d.get("content", "")
        for raw_word in text.split():
            word = "".join(ch for ch in raw_word.lower() if ch.isalnum())
            if len(word) < 3 or word in stopwords:
                continue
            word_counts[word] += 1

    print(f"{Fore.CYAN}========== PDF COLLECTION STATS =========={Style.RESET_ALL}")
    print(f"Total documents : {num_docs}")
    print(f"Total size      : {total_bytes / (1024 * 1024):.2f} MB")
    print(f"Average size    : {avg_bytes / 1024:.1f} KB")

    if oldest and newest:
        print(f"Oldest modified : {oldest.isoformat()}")
        print(f"Newest modified : {newest.isoformat()}")

    print("\nTop 5 folders by document count:")
    for folder, count in folder_counts.most_common(5):
        print(f"  {count:3d}  {folder}")

    print("\nSubject distribution:")
    for subject, count in subject_counts.most_common():
        print(f"  {subject:25s} {count}")

    print("\nTop 10 frequent words (approx):")
    for word, count in word_counts.most_common(10):
        print(f"  {word:15s} {count}")
    print(f"{Fore.CYAN}=========================================={Style.RESET_ALL}")


def interactive_mode(index_path: Path) -> None:
    """
    Simple interactive REPL-style interface for searching the index.
    """
    index_data = load_index(index_path)
    documents = index_data.get("documents", [])

    if not documents:
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Index is empty. Run 'index' first.")
        return

    print(
        f"{Fore.CYAN}Interactive search mode.{Style.RESET_ALL} "
        "Type your query and press Enter. Type 'exit' to quit.\n"
    )

    while True:
        try:
            query = input(f"{Fore.GREEN}>> {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not query:
            continue

        scored_docs = search_documents(documents, query)
        if not scored_docs:
            print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} No matches found.\n")
            continue

        query_terms = [q for q in query.lower().split() if q]

        print(
            f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Found {len(scored_docs)} matching documents. "
            f"Showing top 5:\n"
        )

        for rank, (score, doc) in enumerate(scored_docs[:5], start=1):
            print(f"{Fore.GREEN}#{rank}{Style.RESET_ALL}  (score: {score})")
            print(f"{Fore.CYAN}File   :{Style.RESET_ALL} {doc['filename']}")
            print(f"{Fore.CYAN}Subject:{Style.RESET_ALL} {doc.get('subject', 'Unknown')}")
            snippet = build_snippet(doc["content"], query_terms, max_length=160)
            if snippet:
                print(f"{Fore.MAGENTA}Snippet:{Style.RESET_ALL} {snippet}")
            print("-" * 60)
        print()


def show_menu(default_root: Path, default_index: Path) -> None:
    """
    Simple menu so the user doesn't have to remember commands.
    """
    while True:
        print("\n" + "=" * 50)
        print(" WhatsApp PDF Knowledge Bot - Menu")
        print("=" * 50)
        print("1) Index PDFs")
        print("2) Search PDFs")
        print("3) Interactive Search")
        print("4) Show Stats")
        print("5) Find Duplicates")
        print("6) Exit")
        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            folder_str = input(
                f"Enter folder to index [default: {default_root}]: "
            ).strip()
            folder = Path(folder_str) if folder_str else default_root
            try:
                build_index(folder, default_index, max_pages=3)
            except Exception as e:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {e}")

        elif choice == "2":
            query = input("Enter search query: ").strip()
            if not query:
                print("Empty query, try again.")
                continue
            top_k_str = input("How many results? [default: 5]: ").strip()
            top_k = int(top_k_str) if top_k_str.isdigit() else 5

            export_str = input(
                "Export results? Enter filename (CSV/TXT) or leave blank: "
            ).strip()
            export_path = Path(export_str) if export_str else None

            search_index(
                default_index,
                query,
                top_k=top_k,
                since=None,
                until=None,
                min_size_kb=None,
                max_size_kb=None,
                export=export_path,
            )

        elif choice == "3":
            interactive_mode(default_index)

        elif choice == "4":
            show_stats(default_index)

        elif choice == "5":
            find_duplicates(default_index)

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid choice, please enter a number from 1 to 6.")


def get_default_paths():
    home = Path.home()
    downloads = home / "Downloads"
    if downloads.exists():
        default_root = downloads
    else:
        default_root = Path.cwd()

    default_index = Path.cwd() / "data" / "index.json"
    return default_root, default_index


def main():
    default_root, default_index = get_default_paths()

    parser = argparse.ArgumentParser(
        description="WhatsApp PDF Knowledge Bot - Local PDF search tool"
    )
    subparsers = parser.add_subparsers(dest="command")  # command now optional

    # index command
    index_parser = subparsers.add_parser(
        "index", help="Index all PDFs under a folder"
    )
    index_parser.add_argument(
        "--folder",
        type=Path,
        default=default_root,
        help=f"Root folder to scan for PDFs (default: {default_root})",
    )
    index_parser.add_argument(
        "--index-path",
        type=Path,
        default=default_index,
        help=f"Where to store the index file (default: {default_index})",
    )
    index_parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Max number of pages to read from each PDF (default: 3)",
    )

    # search command
    search_parser = subparsers.add_parser(
        "search", help="Search within the indexed PDFs"
    )
    search_parser.add_argument(
        "query", type=str, help="Search query, e.g. 'unit 4 neural networks'"
    )
    search_parser.add_argument(
        "--index-path",
        type=Path,
        default=default_index,
        help=f"Path to index.json (default: {default_index})",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top results to show (default: 5)",
    )
    search_parser.add_argument(
        "--since",
        type=str,
        help="Only include docs modified on/after this date (YYYY-MM-DD)",
    )
    search_parser.add_argument(
        "--until",
        type=str,
        help="Only include docs modified on/before this date (YYYY-MM-DD)",
    )
    search_parser.add_argument(
        "--min-size-kb",
        type=int,
        help="Only include docs of at least this size in KB",
    )
    search_parser.add_argument(
        "--max-size-kb",
        type=int,
        help="Only include docs of at most this size in KB",
    )
    search_parser.add_argument(
        "--export",
        type=Path,
        help="Export results to given file (CSV or TXT)",
    )

    # stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show statistics and insights about indexed PDFs"
    )
    stats_parser.add_argument(
        "--index-path",
        type=Path,
        default=default_index,
        help=f"Path to index.json (default: {default_index})",
    )

    # dups command
    dups_parser = subparsers.add_parser(
        "dups", help="Find duplicate PDFs based on content"
    )
    dups_parser.add_argument(
        "--index-path",
        type=Path,
        default=default_index,
        help=f"Path to index.json (default: {default_index})",
    )

    # interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Interactive search mode"
    )
    interactive_parser.add_argument(
        "--index-path",
        type=Path,
        default=default_index,
        help=f"Path to index.json (default: {default_index})",
    )

    args = parser.parse_args()

    if args.command is None:
        # No subcommand provided → show menu
        show_menu(default_root, default_index)

    elif args.command == "index":
        build_index(args.folder, args.index_path, max_pages=args.max_pages)

    elif args.command == "search":
        search_index(
            args.index_path,
            args.query,
            top_k=args.top_k,
            since=args.since,
            until=args.until,
            min_size_kb=args.min_size_kb,
            max_size_kb=args.max_size_kb,
            export=args.export,
        )

    elif args.command == "stats":
        show_stats(args.index_path)

    elif args.command == "dups":
        find_duplicates(args.index_path)

    elif args.command == "interactive":
        interactive_mode(args.index_path)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
