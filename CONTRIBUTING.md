# Contributing

This repository is **documentation only**. Please do not open pull requests that add blocklist data, IP lists, Bloom filters, or other feed artifacts. Those files will be published separately, and only after the lists are confirmed reliable.

## Documentation changes

- Open a pull request against `main` with a clear description of the change.
- Keep the tone clear, plain, and practical.
- Do not add secrets, internal hostnames, server paths, or unpublished download URLs presented as live.
- If a format or endpoint is not implemented, label it **planned** or **coming soon** rather than describing it as if it already ships.
- Use only measured performance numbers already recorded in [verae.md](verae.md).

## Nominations and delisting

To nominate an address or ask for a removal, use the forms and API on [blocklist.iprx.org](https://blocklist.iprx.org/) ([Nominate](https://blocklist.iprx.org/nominate), [Remove](https://blocklist.iprx.org/remove); [API](api.md)). Do not open a GitHub issue or pull request with a list of IPs to add or remove, and do not email a personal address for delisting. See [SECURITY.md](SECURITY.md).

## License

Documentation is released under [CC BY 4.0](LICENSE).
