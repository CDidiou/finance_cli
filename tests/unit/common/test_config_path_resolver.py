from finance_cli.config.paths_resolver import ConfigPathResolver


def test_resolve_directory(tmp_config, tmp_path):
    """Résout un répertoire à partir de base_dir et de la configuration."""
    resolver = ConfigPathResolver(tmp_config)

    expected = (tmp_path / "data/assets").resolve()

    assert resolver.resolve_directory("catalog/financial/assets") == expected
