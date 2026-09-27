from src.core.entities import File
from tqdm import tqdm

my_objects: list[File] = list()
def main():
    for idx in tqdm(range(1000)):
        file: File = File(file_path="hello" + str(idx), last_modified_at=idx)
        my_objects.append(file)
        print(file)


if __name__ == "__main__":
    main()
