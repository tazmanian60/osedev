import os
from fabric.api import env, local, run, get, sudo
from fabric.context_managers import shell_env


env.hosts = ['damoti.com']


def prepare():
    """"copy database and migrate"""
    from django.conf import settings
    db = settings.DATABASES['default']
    args = '-h {HOST} -U {USER} {NAME}'.format(**db)
    if db['NAME'] != 'ose_production':
        local('dropdb {}'.format(args))
        local('createdb -T ose_production {}'.format(args))
    local('./manage.py migrate --noinput')
    local('psql -c "VACUUM ANALYZE" {}'.format(args))


def test():
    """django continuous integration test"""
    with shell_env(DJANGO_SETTINGS_MODULE='osedev.settings.test'):
        local('coverage run -p manage.py test -v 2 osedev.apps osedev.lib')
        local('coverage combine')
        local('coverage html -d reports')


def updatecopyright():
    import glob
    from itertools import chain
    paths = [f for f in chain(
        glob.glob('osedev/*.py'),
        glob.glob('osedev/apps/**/*.py', recursive=True),
        glob.glob('osedev/lib/**/*.py', recursive=True),
    ) if 'migrations' not in f]
    license = open('LICENSE').readlines()
    copyright = []
    for line in license[632:646]:
        line = line.strip()
        line = '#  ' + line
        copyright.append(line.strip())
    copyright = '\n'.join(copyright) + '\n\n'
    for fname in paths[1:]:
        lines = iter(open(fname).readlines())
        line = ''
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                break
        with open(fname, 'w') as new:
            new.write(copyright)
            if line:
                new.write(line+'\n')
            new.writelines(lines)


def fetchdb(envname='production'):
    """fetch remote database, see getdb"""
    container = 'damoti_backup_1'
    dbname = 'ose_'+envname
    dump_file = 'osedev.'+envname+'.dump'
    dump_dir = '/var/lib/postgresql/backups'
    dump_path = os.path.join(dump_dir, dump_file)
    # -Fc : custom postgresql compressed format
    run('docker run --rm --network damoti_default -v {dump_dir}:{dump_dir} postgres:10 pg_dump -h postgres -U postgres -Fc -x -f {dump_path} {dbname}'
        .format(**locals()))
    get(dump_path, dump_file)
    sudo('rm {}'.format(dump_path))
    return dump_file


def dbexists(name):
    from django.conf import settings
    db = settings.DATABASES['default']
    dbs = local('psql -p {PORT} -lqt | cut -d \| -f 1'.format(**db), capture=True).split()
    return name in dbs


def getdb(envname='production'):
    """fetch and load remote database"""
    from django.conf import settings
    db = settings.DATABASES['default']
    args = '-p {PORT} {NAME}'.format(**db)
    dump_file = fetchdb(envname)
    if dbexists('ose_local'):
        local('dropdb '+args)
    local('createdb '+args)
    local('pg_restore -p {PORT} -d {NAME} -O {FILE}'.format(FILE=dump_file, **db))
    local('psql -c "ANALYZE" '+args)
    local('rm {}'.format(dump_file))
