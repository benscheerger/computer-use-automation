from automation.capability import MemberLookupInputs
from automation.discovery_job import discover_capability
from automation.task import DiscoveryTask


def main():
    task = DiscoveryTask(
        goal=(
            "Find the requested member's available "
            "savings balance and currency."
        ),
        inputs=MemberLookupInputs(
            member_id="DEMO-101",
        ),
    )

    result = discover_capability(
        task,
        dataset_id="members",
    )

    print("\nDiscovery result:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()