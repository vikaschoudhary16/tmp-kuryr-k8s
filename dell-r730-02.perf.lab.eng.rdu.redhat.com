[tox]
minversion = 2.3.1
envlist = py27,py35,pep8
skipsdist = True

[testenv]
setenv = VIRTUAL_ENV={envdir}
usedevelop = True
install_command = pip install -c{env:UPPER_CONSTRAINTS_FILE:https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt} {opts} {packages}
deps = -r{toxinidir}/requirements.txt
       -r{toxinidir}/test-requirements.txt
whitelist_externals = sh
                      find
commands = find {toxinidir} -type f -name "*.py[c|o]" -delete
           ostestr '{posargs}'

[testenv:fullstack]
basepython = python2.7
setenv = OS_TEST_PATH=./kuryr/tests/fullstack
passenv = OS_*

[testenv:debug]
commands = oslo_debug_helper {posargs}

[testenv:debug-py27]
basepython = python2.7
commands = oslo_debug_helper {posargs}

[testenv:debug-py35]
basepython = python3.5
commands = oslo_debug_helper {posargs}

[testenv:pep8]
commands = flake8

[testenv:venv]
commands = {posargs}

[testenv:cover]
commands =
  python setup.py test --coverage --testr-args='{posargs}' \
    --coverage-package-name=kuryr_kubernetes
  coverage report

[testenv:docs]
commands = python setup.py build_sphinx

[flake8]
# E125 continuation line does not distinguish itself from next logical line
# E126 continuation line over-indented for hanging indent
# E128 continuation line under-indented for visual indent
# E129 visually indented line with same indent as next logical line
# E265 block comment should start with '# '
# TODO(dougwig) -- uncomment this to test for remaining linkages
# N530 direct neutron imports not allowed
# N531 log message does not translate
ignore = E125,E126,E128,E129,E265,H301,N530,N531
show-source = true

# TODO(dougw) neutron/tests/unit/vmware exclusion is a temporary services split hack
exclude = .venv,.git,.tox,dist,doc,*lib/python*,*egg,build,tools,.ropeproject,rally-scenarios,neutron/tests/unit/vmware*

[testenv:pylint]
deps =
  {[testenv]deps}
  pylint
commands =
  pylint --rcfile=.pylintrc --output-format=colorized {posargs:neutron}

[hacking]
import_exceptions = neutron.i18n
local-check-factory = neutron_lib.hacking.checks.factory

[testenv:genconfig]
commands = oslo-config-generator --config-file=etc/oslo-config-generator/kuryr.conf
