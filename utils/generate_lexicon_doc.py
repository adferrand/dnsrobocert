import importlib
import argparse
import os

from lexicon import discovery


def main():
    providers = [provider for provider in discovery.find_providers().keys() if provider != 'auto']

    output = '''\
=========================================
Lexicon providers configuration reference
=========================================

.. contents:: Table of Contents
   :local:

Supported providers
===================

{0}

Options for each provider
=========================

'''.format(', '.join('{0}_'.format(provider) for provider in providers))

    for provider in providers:
        provider_module = importlib.import_module('lexicon.providers.' + provider)
        parser = argparse.ArgumentParser()
        provider_module.provider_parser(parser)

        output = output + '''\
.. _{0}:

{0}
'''.format(provider)

        for action in parser._actions:
            if action.dest == "help":
                continue

            output = output + '''\
  * ``{0}``: {1}
'''.format(action.dest, action.help.capitalize().replace('`', "'"))

        output = output + '\n'

    with open(os.path.join('docs', 'lexicon_providers_config.rst'), 'w') as f:
        f.write(output)


if __name__ == "__main__":
    main()
