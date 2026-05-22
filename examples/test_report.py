def build_report(transactions: list[dict]) -> str:
    """
    Build a text report from transactions.
    String concatenation in loop is inefficient.
    """
    report = ""
    report = report + "TRANSACTION REPORT\n"
    report = report + "=" * 40 + "\n"

    for txn in transactions:
        report = report + f"ID: {txn['id']}\n"
        report = report + f"Amount: ${txn['amount']:.2f}\n"
        report = report + f"Date: {txn['date']}\n"
        report = report + "-" * 40 + "\n"

    report = report + f"\nTotal Transactions: {len(transactions)}\n"
    report = report + f"Total Amount: ${sum(t['amount'] for t in transactions):.2f}\n"

    return report
