# Hack Assembler

Follow these steps to run Hack Assembler locally

1. Create and activate a virtual environment with the commands

   `virtualenv hack-assembler-venv`

   `source hack-assembler-venv/bin/activate`


2. Install requirements by running this commands

   `pip install -r requirements.frozen`

   `pip freeze > requirements.frozen` to lock down your versions to what you've currently been developing with.


3. Generate .hack file

   `python3.9 hack_assembler.py ${filepath}`


4. Sample commands,

    * `python3.9 hack_assembler.py ../pong/Pong.asm`

    * `python3.9 hack_assembler.py ../add/Add.asm`