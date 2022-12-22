from ceci import PipelineStage
from .pipetypes import TextFile
import random
import socket

# - name: CreateNumbers
# - name: AddTwo


class CreateNumbers(PipelineStage):
    
    name = "CreateNumbers"
    inputs = [("dp0_train", TextFile)]
    outputs = [("numbers", TextFile)]
    config_options = {"debug": bool, "rows_number": int, "range": [int, int]}

    def run(self):
        print("Here is my configuration :", self.config)

        dp0 = self.get_input("dp0_train")  # or self.open_input("dp0_train", wrapper=False)
        print("Filename: ", dp0)

        filename = self.get_output('numbers')
        print(f"Writing to {filename}")

        numbers = open(filename, "w")

        ns = self.config['rows_number']
        rg = self.config['range']

        for i in range(int(ns)):
            line = str(random.randint(rg[0], rg[1]))
            numbers.write(line+"\n")

        print(f"Last line: {line}")

        numbers.close()


class AddTwo(PipelineStage):
    name = "AddTwo"
    inputs = [("numbers", TextFile)]
    outputs = [("sum2", TextFile)]

    def run(self):

        numbers = self.get_input("numbers")
        
        with open(numbers) as f:
            lines = f.readlines()

        newlines = []
        for i in lines:
            n = int(i)
            newlines.append(f"{n} + 2 = "+str(n + 2)+"\n")
        
        sum2 = self.get_output('sum2')
        open(sum2, "w").writelines(newlines)


class WLGCCov(PipelineStage):
    name = "WLGCCov"
    inputs = [
        ("numbers", TextFile),
        ("sum2", TextFile),
    ]
    outputs = [("covariance", TextFile)]

    def rank_filename(self, rank, size):
        filename = self.get_output("covariance")

        if size == 1:
            fname = filename
        else:
            fname = f"{filename}.{rank}"
        return fname

    def run(self):

        print("Running WLGCCov in host: " + socket.gethostname())

        # MPI Information
        rank = self.rank
        size = self.size
        comm = self.comm

        for inp, _ in self.inputs:
            filename = self.get_input(inp)
            print(f"    WLGCCov rank {rank}/{size} reading from {filename}")
            open(filename)

        filename = self.get_output("covariance")
        my_filename = self.rank_filename(rank, size)
        print(f"    WLGCCov rank {rank}/{size} writing to {my_filename}")
        open(my_filename, "w").write(f"WLGCCov rank {rank} was here \n")

        #
        if comm:
            comm.Barrier()

        # If needed, concatenate all files
        if rank == 0 and size > 1:
            f = open(filename, "w")
            print(f"Master process concatenating files:")
            for i in range(size):
                fname = self.rank_filename(i, size)
                print(f"   {fname}")
                content = open(fname).read()
                f.write(content)
            f.close()


if __name__ == "__main__":
    cls = PipelineStage.main()
