#!/usr/bin/env python
"""Seed de eventos y usuarios de prueba.

Uso: docker compose exec web python scripts/seed.py
Stub: poblar selecciones, eventos, mercados y cuentas demo. (a implementar)
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def run():
    pass


if __name__ == "__main__":
    run()
