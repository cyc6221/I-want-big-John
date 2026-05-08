from lib_dataset import PREDICTOR_DATA_PATH, build_payload, load_draws, write_payload


def main() -> None:
    payload = build_payload(load_draws())
    write_payload(payload)
    print(f"Updated: {PREDICTOR_DATA_PATH}")
    print(f"   Draws: {payload['summary']['draw_count']}")


if __name__ == "__main__":
    main()
