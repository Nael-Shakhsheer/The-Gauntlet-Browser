"""Portable isolated unittest runner. Never uses or changes the real data/ saves."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temp-root',type=Path,default=ROOT/'.test-tmp')
    parser.add_argument('--pattern',default='test_*.py')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    try:args.temp_root.resolve().relative_to(ROOT/'data')
    except ValueError:pass
    else:parser.error('Test storage must be outside the private data/ directory.')
    args.temp_root.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
    previous=tempfile.tempdir
    with ExitStack() as stack:
        directory=stack.enter_context(tempfile.TemporaryDirectory(prefix='tests-',dir=args.temp_root))
        stack.enter_context(patch.dict(os.environ,{'TEMP':directory,'TMP':directory,'TMPDIR':directory}))
        tempfile.tempdir=directory
        stack.callback(setattr,tempfile,'tempdir',previous)
        # Exercise the exact atomic replacement/OS lock before running assertions.
        from run_storage import locked_record
        test=Path(directory)/'atomic.json';temp=Path(directory)/'atomic.tmp'
        try:
            with locked_record(test):
                with temp.open('wb') as stream:stream.write(b'{}');stream.flush();os.fsync(stream.fileno())
                os.replace(temp,test)
            with locked_record(test):
                test.read_bytes()
                with temp.open('wb') as stream:stream.write(b'{"revision":2}');stream.flush();os.fsync(stream.fileno())
                os.replace(temp,test)
        except OSError as error:
            print('Environment cannot lock/replace test files: '+str(error),file=sys.stderr);return 2
        try:
            with socket.socket() as listener:listener.bind(('127.0.0.1',0))
        except OSError as error:
            print('Environment socket preflight failed; socket tests remain unverified: '+str(error),file=sys.stderr)
        # game constructs a module singleton on import. Redirect only that test
        # import; no production setting, source behavior or private saves change.
        import run_storage
        original=run_storage.RunStorage.__init__
        def isolated(self,_directory):original(self,Path(directory)/'singleton')
        with patch.object(run_storage.RunStorage,'__init__',isolated):import game
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=args.pattern)
        result=unittest.TextTestRunner(verbosity=1).run(suite)
        counts=dict(tests=result.testsRun,passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)-len(result.expectedFailures)-len(result.unexpectedSuccesses),
                    failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),expectedFailures=len(result.expectedFailures),
                    unexpectedSuccesses=len(result.unexpectedSuccesses))
        print(json.dumps(counts),flush=True)
        if args.report:args.report.write_text(json.dumps(counts,indent=2),encoding='utf-8')
        return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
