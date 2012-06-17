TEST_DATA=/home/michal/matref # no trailing slash

./ziptar.py --zip cf _test_arch.zip $TEST_DATA

find $TEST_DATA | while read line; do
    if [ -d "$line" ]; then
        echo $line/
    else
        echo $line
    fi
done | cut -c 2- | sort > _test_found
(echo $TEST_DATA/ | cut -c 2-; ./ziptar.py --zip tf _test_arch.zip) | sort > _test_zip

diff -w _test_found _test_zip || exit 1

mkdir _test_a 2>/dev/null

cd _test_a
../ziptar.py --zip xf ../_test_arch.zip || exit 1
export test_data_len="${#TEST_DATA}"
find | cut -c 2- | while read line; do
    if [ ${#line} -ge $test_data_len ]; then
        echo $line
    fi
done > ../_test_1
cd ..

find $TEST_DATA > _test_2

diff -w _test_1 _test_2 || exit 1

rm -r _test_a
rm _test_*
