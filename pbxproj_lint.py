from mod_pbxproj import XcodeProject
import sys
import os
import logging
import subprocess

logging.getLogger().setLevel(logging.INFO)

MEDIA_EXTENSIONS = ['.jpg',
                    '.png',
                    '.pdf',
                    '.mov',
                    '.mp4']

IGNORE_PATHS = ['PodFile',
                'Podfile.lock',
                'Frameworks',
                '.xcassets',
                '.xcdatamodel',
                '.xcworkspace',
                'xcuserdata',
                '.pbxproj',
                '.git']

def do_lint(pbxproj, is_strict, do_clean):
    logging.info('Analyzing: %s', pbxproj)
    project = XcodeProject.Load(pbxproj)
    errors, warnings = [], []
    for es, ws in [_lint_i18n(project, is_strict),
                   _lint_files(pbxproj, project, do_clean)]:
        errors.extend(es)
        warnings.extend(ws)
    for report, log_fn in [(errors, logging.error),
                           (warnings, logging.warn)]:
        for _, msg in report:
            log_fn(msg)
    logging.info('Done. Errors: %d, Warnings: %d',
                 len(errors), len(warnings))
    if errors:
        sys.exit(1)
    
def _lint_i18n(project, is_strict):
    objects = project.objects
    var_groups = {key: obj for key, obj in objects.iteritems()
                  if obj['isa'] == 'PBXVariantGroup'}
    group_langs = {key: [objects[child]['name'] for child in obj['children']]
                   for key, obj in var_groups.iteritems()}
    all_langs = set(project.root_object['knownRegions'])
    required_langs = all_langs - set(['Base'])
    logging.info('Localizations: %s', ', '.join(sorted(required_langs)))

    errors, warnings = [], []
    for key, langs in group_langs.iteritems():
        if langs == ['Base']:
            # Not localized at all
            continue
        missing_langs = required_langs - set(langs)
        if missing_langs:
            # Image resources might intentionally only be partially localized.
            _, ext = os.path.splitext(objects[key]['name'])
            if not is_strict and ext in MEDIA_EXTENSIONS and langs:
                msg = ('%s might be missing resources\n  Present: %s\n  Missing: %s' %
                       (objects[key]['name'],
                        ', '.join(sorted(group_langs[key])),
                        ', '.join(sorted(missing_langs))))
                warnings.append((key, msg))
            else:
                msg = ('%s is missing resources!\n  Present: %s\n  Missing: %s' %
                       (objects[key]['name'],
                        ', '.join(sorted(group_langs[key])),
                        ', '.join(sorted(missing_langs))))
                errors.append((key, msg))
    return errors, warnings

def _lint_files(pbxproj_path, project, do_clean):
    proj_files = []
    errors = []
    warnings = []

    main_grp = project.root_object['mainGroup']
    xcodeproj_root = os.path.dirname(pbxproj_path)
    proj_root = os.path.abspath(os.path.join(xcodeproj_root,
                                             os.pardir))
    src_root = os.path.abspath(os.path.join(proj_root, os.pardir))
    xcode_root = subprocess.check_output(['xcode-select', '-p']).strip()
    bconf_list_key = project.root_object['buildConfigurationList']
    sdk_ver = next(project.objects[conf]['buildSettings']['SDKROOT']
                   for conf in project.objects[bconf_list_key]['buildConfigurations'])
    sdk_root = subprocess.check_output(['xcrun', '--sdk', sdk_ver,
                                        '--show-sdk-path']).strip()
    logging.debug('SDK version: %s', sdk_ver)
    logging.debug('Xcode root: %s', xcode_root)
    logging.debug('Project root: %s', proj_root)
    logging.debug('Source root: %s', src_root)
    
    def _recurse_tree(key, curr_path):
        node = project.objects[key]
        if 'children' not in node:
            tree = node['sourceTree']
            root = (os.path.join(proj_root, *curr_path) if tree == '<group>'
                    else proj_root if tree == 'SOURCE_ROOT'
                    else xcode_root if tree == 'DEVELOPER_DIR'
                    else sdk_root if tree == 'SDKROOT'
                    else None)
            if root is None:
                logging.debug('File %s is in an unsupported sourceTree: %s',
                              node['path'], tree)
                return
            leaf = os.path.abspath(os.path.join(root, node['path']))
            if not os.path.exists(leaf):
                warnings.append((key, 'Project references a missing file!\n'
                                 '  %s' % leaf))
            proj_files.append(leaf)
        else:
            for child in node['children']:
                _recurse_tree(child, curr_path + [node.get('path', '')])

    _recurse_tree(main_grp, [])

    untracked = []
    pods_root = os.path.join(proj_root, 'Pods')
    for root, _, files in os.walk(proj_root):
        for f in files:
            full_path = os.path.join(root, f)
            if any(ignore in full_path for ignore in [xcodeproj_root,
                                                      pods_root] + IGNORE_PATHS):
                continue
            if full_path not in proj_files:
                untracked.append(full_path)
                if do_clean:
                    os.remove(full_path)
    if untracked:
        warnings.append((None, 'Files present but not referenced by project: '
                         '%d\n  %s' % (len(untracked),
                                       '\n  '.join(untracked))))
    return errors, warnings

def die():
    print 'Usage: pbxproj_lint [--strict] [--clean] PBXPROJ_PATH'
    sys.exit(1)
    
def main():
    args = sys.argv[1:]
    if len(args) not in range(1, 4):
        die()
    infile = args[-1]
    if not os.path.isfile(infile):
        logging.error('Input file not found.')
        die()
    do_lint(infile, '--strict' in args, '--clean' in args)

    
if __name__ == '__main__':
    main()
