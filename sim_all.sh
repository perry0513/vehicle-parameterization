mkdir -p results

for filename in stl/*; do
    name=${filename##*/}
    base=${name%.stl}
    echo "- Running $filename"
    ./run_dexof.sh rough_mesh_4cores_str.dex $filename 0
    mv dir_rough_mesh_4cores_str_aoa_0/results.log results/$base.log
    rm -r dir_rough_mesh_4cores_str_aoa_0
done
