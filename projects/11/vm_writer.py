class VMWriter:
    def __init__(self, output_filepath: str):
        self.__f = open(output_filepath, "w")

    def write_push(self, segment: str, index: int):
        self.__write("push", segment, index)

    def write_pop(self, segment: str, index: int):
        self.__write("pop", segment, index)

    def write_arithmetic(self, command: str):
        self.__write(command)

    def write_label(self, label: str):
        self.__write("label", label)

    def write_goto(self, label: str):
        self.__write("goto", label)

    def write_if(self, label: str):
        self.__write("if-goto", label)

    def write_call(self, name: str, n_args: int):
        self.__write("call", name, n_args)

    def write_function(self, name: str, n_locals: int):
        self.__write("function", name, n_locals)

    def write_return(self):
        self.__write("return")

    def __write(self, *args):
        self.__f.write(" ".join([str(arg) for arg in args]) + "\n")

    def close(self):
        self.__f.close()
