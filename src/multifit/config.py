from importlib import resources

def main():
    container = resources.files('multifit')
    empty_config = container.joinpath('templates', 'empty_input_file.yml').read_text()
    print(empty_config)

if __name__ == '__main__':
    main()
