from lppy.version import version
from lppy.examples.hello import main


def cli():
    print(f"lppy: version={version}")
    main()


if __name__ == "__main__":
    cli()
