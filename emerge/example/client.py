import random
from dataclasses import dataclass
from typing import List

from persistent import Persistent

from emerge.core.client import Client
from emerge.core.objects import EmergeFile
from emerge.data import EmergeData


class MyClass(EmergeFile):
    """Custom class"""

    text = None

    def data(self):
        """Return some data"""
        return self.text

    def run(self):
        return "wordsA:" + str(self.word_count())

    def word_count(self):
        return len(self.text.split(" "))


class Collection(Persistent):

    list: List = []


@dataclass
class InventoryItem(EmergeData):
    """Class for keeping track of an item in inventory."""

    name: str
    unit_price: float
    id: str
    quantity_on_hand: int = 0

    def run(self):
        return "total cost:{}".format(self.total_cost())

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand


""" Here we create a custom object with some data and store/retrieve it.
We do this because we will be asking the network to perform batch calculations on
our custom type using its data and methods """

""" Connect to specific Node """
client = Client("0.0.0.0", "5558")

""" Store a custom instance there """
obj = MyClass(id="myclass", name="myclass", path="/classes")
obj.text = "this is myclass of data"

""" Store an object on a specific node """
client.store(obj)

""" Ask for it back """
obj = client.get("myclass")

""" Execute a method locally on this host """
print("Getting data and word count")
print(obj.data())
print(obj.word_count())
print()

""" Run the object as a service on the remote node """
print("Executing run on server")
print(client.run("myclass", "run"))

item = InventoryItem(id="widget1", name="widget", unit_price=3.0, quantity_on_hand=10)
client.store(item)
print(item)

print(client.run("widget1", "total_cost"))

for i in range(0, 100):
    item = InventoryItem(
        id="widget:" + str(i),
        name="widget",
        unit_price=random.uniform(1.5, 75.5),
        quantity_on_hand=random.randrange(0, 50),
    )
    print(item)
    client.store(item)