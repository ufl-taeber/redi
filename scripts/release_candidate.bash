#!/bin/bash
#
# Release Candidate Helper
#
# This script assists a Releaser in determining if the current develop HEAD is
# ready for release. It should be run from RED-I's root directory.
#
# Usage example:
#  > git checkout 0.13.0; \
#	 NEW_ARGS='--bulk-send-blanks -e' OLD_ARGS='-e' ./release_candidate.bash 0.13.1
#
# Things to do after this runs:
# - was there a clean diff (meaning no changes in output)?
# - verify the overall code coverage has increased or remained the same;
# - verify all tests have passed;
# - verify the pylint score has increased or remained the same;
# - analyze cProfile's call-graph output (callgraph.svg files).
#

function run() {
	OUT=$1
	ADDITIONAL_ARGS=$2
	mkdir $OUT

	make clean
	type deactivate && deactivate
	virtualenv venv
	. venv/bin/activate

	python setup.py develop

	make coverage
	rsync -avP cover/ $OUT/cover/
	make lint
	rsync -avP pylint.out $OUT/pylint.out

	pushd vagrant
	make rc_clean
	make rc_enrollment
	(time python -m cProfile -o ../$OUT/redi.pstats ../redi/redi.py --config-path=../config/ --datadir=../$OUT/datadir --keep ${ADDITIONAL_ARGS}) &> ../$OUT/time
	make rc_get | tee ../$OUT/output.csv
	popd

	(type gprof2dot && type dot && \
		gprof2dot -f pstats $OUT/redi.pstats | dot -T svg -o $OUT/callgraph.svg) || echo WARNING: missing 'gprof2dot' and 'dot'.
}

RELEASE_CANDIDATE=$1
if [ -z ${RELEASE_CANDIDATE} ]
then
	echo "ERROR: please specify the release number."
	echo ''
	echo "Example:	bash ${BASH_SOURCE[0]} 0.12.0"
	exit 1
fi

REDCAP_ZIP=$2


CURRENT_RELEASE=$(git branch | grep "(detached" | grep -o "[[:digit:]][^)]*")

if [ -z ${CURRENT_RELEASE} ]
then
	echo 'ERROR: failed to detect current release.'
	echo ''
	echo "Template: git checkout <TAGGED_VERSION>"
	exit 1
fi

echo "Release candidate version: ${RELEASE_CANDIDATE}"
echo "Current release detected: ${CURRENT_RELEASE}"
sleep 1

if [ ! -d config ]
then
	echo 'WARNING: missing "config" directory. Using "config-example".'
	ln -s config-example config
fi

if [ ! -z ${REDCAP_ZIP} ]
then
	cp $REDCAP_ZIP ./config/vagrant-data/redcap.zip
fi

pushd vagrant
make copy_config_develop
make copy_redcap_code
make copy_project_data
vagrant status | grep running || vagrant up
vagrant provision --provision-with=shell
popd


run release-${CURRENT_RELEASE} ${OLD_ARGS}
git checkout develop
run release-${RELEASE_CANDIDATE} ${NEW_ARGS}
git checkout ${CURRENT_RELEASE}


pushd vagrant
vagrant halt
popd

diff -u release-${CURRENT_RELEASE}/output.csv release-${RELEASE_CANDIDATE}/output.csv

