# ------------------------------------------------------------------------ #
#      o-o      o                o                                         #
#     /         |                |                                         #
#    O     o  o O-o  o-o o-o     |  oo o--o o-o o-o                        #
#     \    |  | |  | |-' |   \   o | | |  |  /   /                         #
#      o-o o--O o-o  o-o o    o-o  o-o-o--O o-o o-o                        #
#             |                           |                                #
#          o--o                        o--o                                #
#                        o--o      o         o                             #
#                        |   |     |         |  o                          #
#                        O-Oo  o-o O-o  o-o -o-    o-o o-o                 #
#                        |  \  | | |  | | |  |  | |     \                  #
#                        o   o o-o o-o  o-o  o  |  o-o o-o                 #
#                                                                          #
#    Jemison High School - Huntsville Alabama                              #
# ------------------------------------------------------------------------ #

import os
import sys

__is_k8s = os.environ.get('K8S', 'False') == 'True'
__dbg_host = os.environ.get('PYDEVD_HOST', '0.0.0.0').strip()  # nosec
__dbg_port = os.environ.get('PYDEVD_PORT', '0').strip()

if __dbg_host != '0.0.0.0' and __dbg_port not in ('', '0'):  # nosec
    try:
        import pydevd_pycharm

        # Initial breakpoint if suspend = True
        print(f'Loading pydevd debugger for {__dbg_host}:{__dbg_port}')
        pydevd_pycharm.settrace(__dbg_host, port=int(__dbg_port), stdoutToServer=True,
                                stderrToServer=True, suspend=False)
    except ImportError:
        print(f'Error importing pydevd package. {sys.exc_info()[0]}')
        print('REMOTE DEBUGGING will not be supported in this run...')
        # Continue on...

    except AttributeError:
        print('Attribute error. Perhaps try to explicitly set PYTHONPATH to'
              'pydevd directory and run again?')
        print('REMOTE DEBUGGING will not be supported in this run...')
        # Continue on...

    except ConnectionRefusedError as e:
        print(f"Pydevd connection to {__dbg_host}:{__dbg_port} refused: {e}")
        print('REMOTE DEBUGGING will not be supported in this run...')
        # Continue on...

    except Exception:
        print(f"pydevd startup exception: {sys.exc_info()[0]}")
        print('REMOTE DEBUGGING will not be supported in this run...')


def debug_enable() -> None:
    """ Call this during startup to load remote debug support """
    if __dbg_host != '0.0.0.0' and __dbg_port not in ('', '0'):  # nosec
        print("")  # Just a convenient place for a breakpoint to be set if you need it
