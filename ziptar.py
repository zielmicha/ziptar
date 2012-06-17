#!/usr/bin/env python
# ZipTar archive manager
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys
import zipfile
import tarfile
import os
import shutil

flags = [
    ('zip', '--zip'),
    ('create', '--create', 'c'),
    ('extract', '--extract', 'x'),
    ('list', '--list', 't'),
    ('gzip', '--gzip', 'g'),
    ('bzip', '--bzip', 'j'),
    ('file', '--file', 'f'),
    #('unsafe', '--unsafe'),
]

def parse_args():
    args = sys.argv[1:]

    options = []
    positional = []

    for i, arg in enumerate(args):
        if arg == '--':
            positional += args[i + 1:]
            break
        elif arg.startswith('--'):
            options.append(arg)
        else:
            positional.append(arg)

    flags_dict = dict(sum(
            [
                [(item, flag_tuple[0]) for item in flag_tuple[1:]] for flag_tuple in flags
            ], []
    ))
    result = {}
    
    if len(positional) < 1:
        help()
    
    for char in positional[0]:
        try:
            name = flags_dict[char]
        except KeyError:
            print >>sys.stderr, 'undefined flag character', char
            help()
        result[name] = True

    for option in options:
        try:
            name = flags_dict[option]
        except KeyError:
            print >>sys.stderr, 'undefined option', option
            help()
        result[name] = True

    return result, positional[1:]

def help():
    s = 'Usage: ziptar flags [options] [archive] [files]\n'

    for flag_tuple in flags:
        desc = ' '.join( flag_tuple[1:] )
        s += '\t%s%s\n' % (desc.ljust(20), flag_tuple[0])
    
    sys.exit(s)

def main():
    options, args = parse_args()

    bzip = options.get('bzip')
    gzip = options.get('gzip')

    if [gzip, bzip].count(True) > 1:
        sys.exit('error: cannot use more than one compression format')

    compression = ('gzip' if gzip else ('bzip' if bzip else 'none'))
    
    create = options.get('create')
    extract = options.get('extract')
    list = options.get('list')
    
    if [create, extract, list].count(True) > 1:
        sys.exit('error: cannot do two things at once')
        
    if [create, extract, list].count(True) == 0:
        sys.exit('error: need to specify action - create, extract or list')
        
    use_file = options.get('file')

    if use_file:
        file_name = args[0]
        args = args[1:]
        def open_file(mode):
            return open(file_name, mode)
    else:
        def open_file(mode):
            if mode == 'r':
                return sys.stdin
            elif mode == 'w':
                return sys.stdout
            else:
                raise ValueError

    zip = options.get('zip')
    tar = not zip
    archive_type = 'zip' if zip else 'tar'

    if not tar and (bzip or gzip):
        sys.exit('error: gzip and bzip only makes sense with tar archives')

    if bzip:
        archive_type += '.bz2'
    elif gzip:
        archive_type += '.gz'
    
    if extract and args:
        sys.exit('error: not expected any argument when extracting')

    if list and args:
        sys.exit('error: not expected any argument when listing')

    if create and not args:
        sys.exit('error: cowardly refusing to create an empty archive')

    if create:
        create_archive(archive_type, open_file('w'), args)
    elif list:
        list_archive(archive_type, open_file('r'))
    else:
        extract_archive(archive_type, open_file('r'))
        
def create_archive(type, file, members):
    if type.startswith('tar'):
        _create_tar_archive(type[4:], file, members)
    elif type == 'zip':
        _create_zip_archive(file, members)
    else:
        raise ValueError

def _create_zip_archive(file, members):
    with zipfile.ZipFile(file, 'w') as f:
        for path in _walk(members, dirs=False):
            f.write(path)

def _create_tar_archive(type, file, members):
    compression = {'bzip': 'bz2', 'gzip': 'gz', '': ''}[type]
    with tarfile.open(fileobj=file, mode='w|' + compression) as f:
        for path in members:
            f.add(path, recursive=True)
            
def _walk(members, dirs=False):
    for member in members:
        for root, dirs, files in os.walk(member):
            for file in files:
                yield os.path.join(root, file)
            if dirs:
                for dir in dirs:
                    yield os.path.join(root, dir)
    
def extract_archive(type, file):
    if type.startswith('tar'):
        _extract_tar_archive(type[4:], file)
    elif type == 'zip':
        _extract_zip_archive(file)
    else:
        raise ValueError

def _extract_zip_archive(file):
    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        return _extract_member(self, member, path, pwd)

    def _extract_member(self, member, targetpath, pwd):
        # modified ZipFile._extract_memeber
        """Extract the ZipInfo object 'member' to a physical
           file on the path targetpath.
        """
        # build the destination pathname, replacing
        # forward slashes to platform specific separators.
        # Strip trailing path separator, unless it represents the root.
        if (targetpath[-1:] in (os.path.sep, os.path.altsep)
            and len(os.path.splitdrive(targetpath)[1]) > 1):
            targetpath = targetpath[:-1]

        targetpath = os.path.normpath(targetpath)

        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)

        if member.filename[-1] == '/':
            if not os.path.isdir(targetpath):
                os.mkdir(targetpath)
            return targetpath

        source = self.open(member, pwd=pwd)
        target = open(targetpath, "wb")
        shutil.copyfileobj(source, target)
        source.close()
        target.close()

        return targetpath
    
    with zipfile.ZipFile(file, 'r') as f:
        for name in f.namelist():
            extract(f, name, _name_to_path(name))
            
def _extract_tar_archive(type, file):
    with tarfile.open(fileobj=file, mode='r|*') as f:
        raise RuntimeError('not yet implemented')

def list_archive(type, file):
    if type.startswith('tar'):
        _list_tar_archive(type[4:], file)
    elif type == 'zip':
        _list_zip_archive(file)
    else:
        raise ValueError

def _list_zip_archive(file):
    with zipfile.ZipFile(file, 'r') as f:
        for name in f.namelist():
            print name

def _list_tar_archive(type, file):
    with tarfile.open(fileobj=file, mode='r|*') as f:
        raise RuntimeError('not yet implemented')
    
def _name_to_path(path):
    stack = []
    for name in path.split('/'):
        if name in ('.', ''):
            pass
        elif name == '..':
            if stack:
                stack.pop()
        else:
            stack.append(name)
    return '/'.join(stack)
            
if __name__ == '__main__':
    main()
