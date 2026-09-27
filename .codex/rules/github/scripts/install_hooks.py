"""Install the push guard in the Git common directory, without replacing hooks."""

import os
from pathlib import Path
import subprocess
import sys


SOURCE = Path(__file__).resolve().parents[1] / 'hooks' / 'pre-push'


def git(*args, missing_ok=False):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode and not (missing_ok and result.returncode == 1):
        raise ValueError('Git設定を取得・更新できませんでした。')
    return result.stdout.strip()


def install():
    common = Path(git('rev-parse', '--git-common-dir')).resolve()
    destination = common / 'kizuki-hooks'
    target = destination / 'pre-push'
    # Worktree overrides can shadow shared configuration; do not silently disable them.
    if git('config', '--bool', '--get', 'extensions.worktreeConfig', missing_ok=True) == 'true':
        raise ValueError('worktree個別設定が有効です。hooksPath競合を手動で解消してください。')
    configured = git('config', '--get-all', 'core.hooksPath', missing_ok=True).splitlines()
    expected_path = destination.as_posix()
    if configured and configured != [expected_path]:
        raise ValueError('既存のcore.hooksPathと競合するため変更しません。')
    default_hooks = common / 'hooks'
    if default_hooks.is_symlink():
        raise ValueError('既存hooksがsymlinkのため変更しません。')
    if default_hooks.exists():
        if any(not p.name.endswith('.sample') for p in default_hooks.iterdir()):
            raise ValueError('既存hookと競合するため変更しません。')
    if destination.is_symlink() or target.is_symlink():
        raise ValueError('設置先がsymlinkのため変更しません。')
    content = SOURCE.read_bytes().replace(b'\r\n', b'\n')
    if destination.exists():
        if set(p.name for p in destination.iterdir()) != {'pre-push'}:
            raise ValueError('設置先に別のファイルがあるため変更しません。')
        if target.read_bytes() != content:
            raise ValueError('設置済みhookと内容が異なるため変更しません。')
    else:
        destination.mkdir()
        with target.open('xb') as stream:
            stream.write(content)
    target.chmod(0o755)
    if os.name != 'nt' and not os.access(target, os.X_OK):
        raise ValueError('hookの実行権限を設定できませんでした。')
    git('config', '--local', 'core.hooksPath', expected_path)
    print('共通Gitディレクトリにpre-pushを設置しました。')


def main():
    try:
        install()
        return 0
    except (OSError, ValueError) as error:
        print(f'設置できませんでした: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
