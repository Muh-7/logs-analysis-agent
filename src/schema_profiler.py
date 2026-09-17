from collections import Counter, defaultdict


class SchemaProfiler:
    def __init__(self):
        self.total_events = 0
        self.decoder_counts = Counter()

        # Fields found inside "data" for every decoder
        self.data_fields = defaultdict(Counter)

        # Number of events that actually contain "data"
        self.data_events = Counter()

    def process(self, log: dict):
        self.total_events += 1

        decoder = log.get("decoder", {}).get("name", "UNKNOWN")

        self.decoder_counts[decoder] += 1

        data = log.get("data")

        if not isinstance(data, dict):
            return

        self.data_events[decoder] += 1

        for field in data.keys():
            self.data_fields[decoder][field] += 1

    def process_logs(self, logs):
        for log in logs:
            self.process(log)

    def report(self, top_decoders=20, top_fields=30):

        print(f"\nTotal events: {self.total_events:,}")

        for decoder, count in self.decoder_counts.most_common(top_decoders):

            print("\n" + "=" * 70)
            print(f"Decoder: {decoder}")
            print(f"Total events: {count:,}")

            data_count = self.data_events[decoder]

            print(f"Events with data: {data_count:,}")

            if data_count == 0:
                print("No data fields.")
                continue

            print("\nFields:")

            for field, field_count in self.data_fields[
                decoder
            ].most_common(top_fields):

                percentage = (
                    field_count / data_count
                ) * 100

                print(
                    f"{field:<35}"
                    f"{field_count:>10,}"
                    f"   {percentage:6.2f}%"
                )