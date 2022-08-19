rm result.csv
touch result.csv

echo "Name,Df,Cd,Ra" >> result.csv

for filename in results/*; do
    name=${filename##*/}
    base=${name%.stl}
    Df=`grep Total $filename | head -n 1 | awk '{print $3}'`
    Df=${Df:1}

    Cd=`grep Cd $filename | awk '{print $3}'`
    Ra=`grep Aref $filename | head -n 2 | tail -n 1 | awk '{print $4}'`
    echo $Df, $Cd, $Ra
    echo "$base,$Df,$Cd,$Ra" >> result.csv
done
