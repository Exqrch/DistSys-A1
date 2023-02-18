import logging
import threading
from pprint import pformat

from node_socket import UdpSocket

class Order:
    RETREAT = 0
    ATTACK = 1


class General:

    def __init__(self, my_id: int, is_traitor: bool, my_port: int,
                 ports: list, node_socket: UdpSocket, city_port: int):
        self.ports = ports
        self.my_id = my_id
        self.city_port = city_port
        self.node_socket = node_socket
        self.my_port = my_port
        self.is_traitor = is_traitor
        self.orders = []

    def start(self):
        """
        TODO
        :return: None
        """
        logging.info(f"general {self.my_id} Start listening for incoming messages...")
        supreme_order = self.listen_procedure()[1]

        # Relay supreme general's order
        self.sending_procedure(sender=self.my_id, order=supreme_order)

        # Listen from 2 other general's given order
        order1 = self.listen_procedure()
        order2 = self.listen_procedure()
        self.conclude_action(orders = self.orders)
        return None

    def listen_procedure(self):
        """
        TODO
        :return: list
        """
        while True:
            message, address = self.node_socket.listen()
            if message == "ALIVE?":
                self.node_socket.send(message="1", port=self.ports[0])
            else:
                message = message.split(';')
                sender_id, sender_order = int(message[0]), int(message[1])
                if sender_id == 0:
                    logging.info(f"general {self.my_id} Got incoming message from supreme_general: ['supreme_general', 'order={sender_order}']")
                else:
                    logging.info(f"general {self.my_id}  Got incoming message from general {sender_id}: ['general {sender_id}', 'order={sender_order}']")
                self.orders.append(sender_order)
                logging.info(f"general {self.my_id} Append message to a list: {self.orders}")
                return [sender_id, sender_order]

    def sending_procedure(self, sender, order):
        """
        TODO
        :param sender: sender id
        :param order: order
        :return: str or None
        """
        def thread_func(order, target_id, port):
            logging.info(f"general {self.my_id} Initiate threading to send the message...")
            logging.info(f"general {self.my_id} Start threading...")
            self.node_socket.send(message=f"{self.my_id};{order}", port=port)
            logging.info(f"general {self.my_id} Done sending message to general {target_id}...")

        if self.is_traitor:
            if order:
                order = 0
            else:
                order = 1

        logging.info(f"general {self.my_id} Send supreme general order to other generals with threading...")
        logging.info(f"general {self.my_id} message: general_{self.my_id}~order={order}")

        target_ports = [(i, port) for i, port in enumerate(self.ports)]
        target_ports = target_ports[1:]
        target_ports = [port for port in target_ports if port[1] != self.my_port]

        thread1 = threading.Thread(target=thread_func, args=(order, target_ports[0][0], target_ports[0][1]))
        thread2 = threading.Thread(target=thread_func, args=(order, target_ports[1][0], target_ports[1][1]))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        return None

    def conclude_action(self, orders):
        """
        TODO
        :param orders: list
        :return: str or None
        """
        order = -1
        logging.info(f"general {self.my_id} Concluding action...")
        if self.is_traitor:
            logging.info(f"general {self.my_id} I am a traitor...")
        else:
            if sum(orders) > len(orders)/2:
                logging.info(f"general {self.my_id} action: ATTACK")
                order = 1
            else:
                logging.info(f"general {self.my_id} action: RETREAT")
                order = 0
            logging.info(f"general {self.my_id} Done doing my action...")
            # City sees my action as well
            self.node_socket.send(message=f"{self.my_id};{order}" ,port=self.city_port)

        return None


class SupremeGeneral(General):

    def __init__(self, my_id: int, is_traitor: bool, my_port: int, ports: list, node_socket: UdpSocket, city_port: int,
                 order: Order):
        super().__init__(my_id, is_traitor, my_port, ports, node_socket, city_port)
        self.order = order

    def sending_procedure(self, sender, order):
        """
        TODO
        :param sender: sender id
        :param order: order
        :return: list
        """
        target_ports = [port for port in self.ports if port != self.my_port]

        # Message structure: sender_id;order.
        if self.is_traitor:
            for i, port in enumerate(target_ports):
                logging.info(f"Send message to general {i+1} with port {port}")
                if (i+1) % 2 == 1:
                    self.node_socket.send(message=f"{self.my_id};1", port=port)
                else:
                    self.node_socket.send(message=f"{self.my_id};0", port=port)
        else:
            for i, port in enumerate(target_ports):
                logging.info(f"Send message to general {i+1} with port {port}")
                self.node_socket.send(message=f"{self.my_id};{order}", port=port)

        return []

    def start(self):
        """
        TODO:
            1. A supreme general only sends message and will receive no message
            2. The supreme general will relay it's decision to every other general depending
               if the supreme general is a traitor or not.
            3. The supreme general will announce what they will do to the city
        :return: None
        """
        # Get target ports
        target_ports = [port for port in self.ports if port != self.my_port]

        logging.info(f"Supreme general is starting...")
        logging.info(f"Wait until all generals are running...") #How?

        ports_status = [0, 0, 0]
        self.node_socket.sc.settimeout(1)
        while (ports_status != [1, 1, 1]):
            for i, port in enumerate(target_ports):
                try:
                    self.node_socket.send(message="ALIVE?", port=port)
                    data, _ = self.node_socket.listen()
                    ports_status[i] = 1
                except:
                    ports_status[i] = 0


        # All generals are now running!
        self.sending_procedure(sender=self.my_id, order=self.order)
        self.conclude_action(orders=self.order)

        return None

    def conclude_action(self, orders):
        """
        TODO
        :param orders: list
        :return: str or None
        """
        logging.info(f"Concluding action...")
        if self.is_traitor:
            logging.info(f"I am a traitor...")
        else:
            if orders == "ATTACK":
                logging.info("ATTACK the city...")
            else:
                logging.info("RETREAT from the city...")
            logging.info("Send information to city...")
            self.node_socket.send(message=f"{self.my_id};{orders}", port=self.city_port)
            logging.info("Done sending information...")

        return None


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def main(is_traitor: bool, node_id: int, ports: list,
         my_port: int = 0, order: Order = Order.RETREAT,
         is_supreme_general: bool = False, city_port: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        if node_id > 0:
            logging.info(f"General {node_id} is running...")
        else:
            logging.info("Supreme general is running...")
        logging.debug(f"is_traitor: {is_traitor}")
        logging.debug(f"ports: {pformat(ports)}")
        logging.debug(f"my_port: {my_port}")
        logging.debug(f"order: {order}")
        logging.debug(f"is_supreme_general: {is_supreme_general}")
        logging.debug(f"city_port: {city_port}")

        if node_id == 0:
            obj = SupremeGeneral(my_id=node_id,
                                 city_port=city_port,
                                 is_traitor=is_traitor,
                                 node_socket=UdpSocket(my_port),
                                 my_port=my_port,
                                 ports=ports, order=order)
        else:
            obj = General(my_id=node_id,
                          city_port=city_port,
                          is_traitor=is_traitor,
                          node_socket=UdpSocket(my_port),
                          my_port=my_port,
                          ports=ports, )
        obj.start()
    except Exception:
        logging.exception("Caught Error")
        raise
