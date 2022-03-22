from sklearn.model_selection import train_test_split
from specification import Specification
from typing import List, Dict
import json
from multiprocessing import Pool, cpu_count
from pandas import DataFrame

def worker(datas : List[Dict[str, str]]) -> None:
    err_id: List[int] = []
    results: List[Dict[str, str]] = []

    for data in datas:
        spec: Dict[str,str] = None
        try:
            spec : Specification = Specification(data)
            for pair in spec.tagged_sentence_list:
                results.append({
                    "source_sequence": pair[0],
                    "target_sequence" : pair[1],
                    "title" : spec.title,
                    "value_info" : spec.axis_title,
                    "chart_type" : spec.chart_type,
                    "table" : spec.table.to_csv(index=True),
                })
                
        except:
            err_id.append(data["id"])
    return err_id, results


if __name__ == "__main__":
    print(f"Generate Source Sequence and Target Sequence from Raw Dataset (User Selection)")
    corenum = cpu_count()
    data_length = 0

    data_schemas: List[Dict[str, str]] = []
    with open("./data/statista.json", "r") as f:
        data_schemas = json.load(f)

    limit = len(data_schemas) // (corenum - 1)
    splited_data = [data_schemas[i*limit: (i+1)*limit] for i in range(corenum)]
    print("=" * 50)
    print(f"Dataset Size : {len(data_schemas)}\nNumber of processes: {corenum}\nNumber of data per thread: {limit}")
    print("=" * 50)
    print("Processing...")

    pool = Pool(processes=corenum)
    result_pool = pool.map(worker, splited_data)
    pool.close()
    pool.join()

    res = []
    err = []
    for err_id, results in result_pool:
        res += results
        err += err_id

    print("=" * 50)
    print(f"Number of data processed: {len(res)}")
    print(f"Number of data error: {len(err)}")
    print("=" * 50)
    print("Convert To DataFrame...")
    res_df : DataFrame = DataFrame({
        "source_sequence" : [data["source_sequence"] for data in res],
        "target_sequence" : [data["target_sequence"] for data in res],
        "title" : [data["title"] for data in res],
        "value_info" : [data["value_info"] for data in res],
        "chart_type" : [data["chart_type"] for data in res],
        "table" : [data["table"] for data in res],
    })
    err_df : DataFrame = DataFrame({
        "id" : err,
    })
    train_df, test_df = train_test_split(res_df, test_size=0.2, random_state=42)


    print("Writing File... ")
    try:
        res_df.to_csv("./data/statista_all.csv", index=True)
        train_df.to_csv("./data/statista_train_valid.csv", index=True)
        test_df.to_csv("./data/statista_test.csv", index=True)
        err_df.to_csv("./data/statista_err.csv", index=True)
    except:
        print("Writing file error")