#!/usr/bin/env python3

import sys
import os
import re
import json
import yaml

SHOW_USAGE = True


def usage():
    return "\n".join([
            f"Usage: {sys.argv[0].split('/')[-1]} <filename>",
            "<filename>\t- path to file with JSON or YAML inside, which be converted into another format"
    ])


def err_exit(err_msg, show_usage=False):
    if show_usage:
        err_msg = f"{err_msg}\n{usage()}"
    raise SystemExit(f"Error: {err_msg}")


def guess_file_type(guess_file):
    # return: ('json'|'yaml'|'unknown')

    with open(guess_file, 'r') as fd:
        content = fd.readlines()

    guessed_type = ''
    content_line = ''
    while True:
        try:
            content_line = content[0]
        except IndexError:
            err_exit(f"No useful content found in {guess_file}")

        # try to avoid YAML comments
        if re.match(r'^\s*#', content_line):
            del(content[0])
            continue

        if re.match(r'^\s*[\[{]', content_line):
            guessed_type = 'json'
        elif re.match(r'^---', content_line):
            guessed_type = 'yaml'
        else:
            guessed_type = 'unknown'
        break

    return guessed_type


def json2yaml(json_file):
    with open(json_file, 'r') as fd:
        try:
            parsed_content = json.load(fd)
        except ValueError as e:
            error_line = e.doc.split('\n')[e.lineno - 1]
            # ("При обнаружении ошибки в исходном файле -
            # указать в стандартном выводе строку с ошибкой синтаксиса и её номер")
            # но тут логичней использовать STDERR, ошибка жеж! да и функцию уже нарисовали.
            err_exit(
                f"File '{json_file}' JSON decode error:\n" +
                f"{e.msg}, in line {e.lineno}, column {e.colno}:\n" +
                f"{error_line}\n{' ' * (e.colno - 1)}^"
            )

    # ("Полученный файл должен иметь имя исходного файла,
    # разница в наименовании обеспечивается разницей расширения файлов")
    output_file_name = os.path.splitext(json_file)[0] + '.yaml'
    with open(output_file_name, 'w') as fd:
        fd.write(yaml.dump(parsed_content, explicit_start=True))
    print(f"JSON file '{json_file}' has been converted into YAML '{output_file_name}'")
    return


def yaml2json(yaml_file):
    with open(yaml_file, 'r') as fd:
        try:
            parsed_content = yaml.safe_load(fd.read())
        except yaml.YAMLError as e:
            # ("При обнаружении ошибки в исходном файле -
            # указать в стандартном выводе строку с ошибкой синтаксиса и её номер")
            # но тут логичней использовать STDERR, ошибка жеж! да и функцию уже нарисовали.
            err_exit(e)

    # ("Полученный файл должен иметь имя исходного файла,
    # разница в наименовании обеспечивается разницей расширения файлов")
    output_file_name = os.path.splitext(yaml_file)[0] + '.json'
    with open(output_file_name, 'w') as fd:
        fd.write(json.dumps(parsed_content, indent=1))
    print(f"YAML file '{yaml_file}' has been converted into JSON '{output_file_name}'")
    return


# get filename parameter
# ("Принимать на вход имя файла")
file_name = ''
try:
    file_name = sys.argv[1]
except IndexError:
    err_exit("Please provide a file name", SHOW_USAGE)

if not os.path.isfile(file_name):
    err_exit(f"File {file_name} doesn't exist or not a file")

# ("Проверять формат исходного файла. Если файл не json или yml - скрипт должен остановить свою работу")
# check for valid file extension
file_ext = os.path.splitext(file_name)[-1]
if not file_ext.lower() in ['.json', '.yaml', '.yml']:
    err_exit(f"Wrong file extension '{file_ext}'")

# detect file format
real_file_type = guess_file_type(file_name)
if real_file_type == 'unknown':
    err_exit(f"Can't detect data format in {file_name}")

# ("Перекодировать данные из исходного формата во второй доступный (из JSON в YAML, из YAML в JSON)")
if real_file_type == 'json':
    json2yaml(file_name)

if real_file_type == 'yaml':
    yaml2json(file_name)

print("Done.")
