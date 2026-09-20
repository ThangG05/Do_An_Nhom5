"""Smoke-test the deployed Modal BGE-M3 class without printing vector values."""
import modal


def main() -> None:
    deployed_class = modal.Cls.from_name("hvnh_rag", "BgeM3")
    result = deployed_class().embed.remote(
        ["Quy chế đào tạo của Học viện Ngân hàng."],
        "document",
    )
    print("modal_embedding=ok")
    print(
        f"model={result['model']}, vectors={result['count']}, "
        f"dimensions={result['dimensions']}"
    )


if __name__ == "__main__":
    main()
