name = "bb_multimesh_showcase"

version = "0.1.0"

authors = [
    "Bonny Baez",
    "Jeremy Andriambolisoa",
]

description = \
    """
    This script duplicates a mesh and creates a blend shape deformer for each duplicate. 
    """


requires = [
    "python-3+",
    "maya-2025+"
]

uuid = "BonnyBaez.bb_multimesh_showcase"

build_command = 'python {root}/build.py {install}'

def commands():
    env.PYTHONPATH.append("{root}/python/")
    