#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for the PerfmonV3 application.
::author:: Ruilx
"""

import asyncio
import os
import pathlib

import click

@click.command()
@click.option("-c", "--config", type=click.Path(exists=True), required=True, help="Path to the configuration file.")
@click.option("-l", "--log", type=click.Path(file_okay=False), multiple=True, default=['_stderr'], help="Directory for log files.")
@click.option("--log-level", type=click.Choice(LogLevel.keys()), default="DEBUG", help="Set the logging level.")
def main(config, log, log_level):
