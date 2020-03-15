import importlib
import argparse
import os

from lexicon import discovery


def main():
    output = '''\
=========================================
Lexicon providers configuration reference
=========================================

'''
    for provider in discovery.find_providers().keys():
        if provider == 'auto':
            continue

        provider_module = importlib.import_module('lexicon.providers.' + provider)
        parser = argparse.ArgumentParser()
        provider_module.provider_parser(parser)

        output = output + '''\
{0}
{1}

'''.format(provider, '=' * len(provider))

        for action in parser._actions:
            if action.dest == "help":
                continue

            output = output + '''\
* ``{0}``: {1}
'''.format(action.dest, action.help.capitalize())

        output = output + '\n'

    with open(os.path.join('docs', 'lexicon_providers_config.rst'), 'w') as f:
        f.write(output)


if __name__ == "__main__":
    main()
