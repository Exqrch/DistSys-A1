import logging
import threading
import time
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
        logging.info(f"Start listening for incoming messages...")
        ret = self.listen_procedure()
        sender, supreme_order = ret[0], ret[1]
        # Relay supreme general's order
        self.sending_procedure(sender=sender, order=supreme_order)

        # Listen from 2 other general's given order
        ret = self.listen_procedure()
        sender, order1 = ret[0], ret[1]
        self.sending_procedure(sender=sender, order=order1)
        ret = self.listen_procedure()
        sender, order2 = ret[0], ret[1]
        self.sending_procedure(sender=sender, order=order2)
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
                message = message.split('~')
                sender, sender_order = message[0], message[1]
                if sender == "supreme_general":
                    logging.info(f"Got incoming message from supreme_general: ['supreme_general', 'order={sender_order}']")
                else:
                    logging.info(f"Got incoming message from {sender}: ['{sender}', 'order={sender_order}']")
                self.orders.append(int(sender_order.split('=')[-1]))
                logging.info(f"Append message to a list: {self.orders}")
                return [sender, sender_order]
            self.node_socket.sc.close()

        return [-1, -1]

    def sending_procedure(self, sender, order):
        """
        TODO
        :param sender: sender id
        :param order: order
        :return: str or None
        """
        def thread_func(order, target_id, port):
            logging.info(f"Initiate threading to send the message...")
            logging.info(f"Start threading...")
            self.node_socket.send(message=f"general_{self.my_id}~order={order}", port=port)
            logging.info(f"Done sending message to general {target_id}...")
            return f"general_{self.my_id}~order={order}"

        if sender != "supreme_general":
            return None

        if self.is_traitor:
            if order:
                order = 0
            else:
                order = 1

        logging.info(f"Send supreme general order to other generals with threading...")
        logging.info(f"message: general_{self.my_id}~order={order}")

        target_ports = [(i, port) for i, port in enumerate(self.ports)]
        target_ports = target_ports[1:]
        target_ports = [port for port in target_ports if port[1] != self.my_port]

        thread1 = threading.Thread(target=thread_func, args=(order, target_ports[0][0], target_ports[0][1]))
        thread2 = threading.Thread(target=thread_func, args=(order, target_ports[1][0], target_ports[1][1]))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        return f"general_{self.my_id}~order={order}"

    def conclude_action(self, orders):
        """
        TODO
        :param orders: list
        :return: str or None
        """
        order = -1
        logging.info(f"Concluding action...")
        if self.is_traitor:
            logging.info(f"I am a traitor...")
        else:
            if sum(orders) > len(orders)/2:
                logging.info(f"action: ATTACK")
                order = 1
            else:
                logging.info(f"action: RETREAT")
                order = 0
            logging.info(f"Done doing my action...")
            # City sees my action as well
            self.node_socket.send(message=f"general_{self.my_id}~order={order}", port=self.city_port)

        return f"general_{self.my_id}~action={order}"


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
        orders = []
        # Message structure: sender_id;order.
        if self.is_traitor:
            for i, port in enumerate(target_ports):
                logging.info(f"Send message to general {i+1} with port {port}")
                if (i+1) % 2 == 1:
                    self.node_socket.send(message=f"supreme_general~order=1", port=port)
                    orders.append(1)
                else:
                    self.node_socket.send(message=f"supreme_general~0", port=port)
                    orders.append(0)
        else:
            for i, port in enumerate(target_ports):
                logging.info(f"Send message to general {i+1} with port {port}")
                self.node_socket.send(message=f"supreme_general~{order}", port=port)
                orders.append(order)

        logging.info(f"Finish sending message to other generals...")

        return orders

    def start(self, robust_check=False):
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

        if robust_check:
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
        else:
            time.sleep(0.5)



        # All generals are now running!
        self.sending_procedure(sender=self.my_id, order=self.order)
        self.conclude_action(orders=self.order)
        logging.shutdown()

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
            if orders:
                logging.info("ATTACK the city...")
            else:
                logging.info("RETREAT from the city...")
            logging.info("Send information to city...")
            self.node_socket.send(message=f"supreme_general~{orders}", port=self.city_port)
            logging.info("Done sending information...")
            return f"supreme_general~action={self.order}"


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

def reload_logging_config_node(filename):

    from importlib import reload
    reload(logging)
    logging.basicConfig(format='%(asctime)-4s %(levelname)-6s %(threadName)s:%(lineno)-3d %(message)s',
                        datefmt='%H:%M:%S',
                        filename=f"logs/{filename}",
                        filemode='w',
                        level=logging.INFO)

def main(is_traitor: bool, node_id: int, ports: list,
         my_port: int = 0, order: Order = Order.RETREAT,
         is_supreme_general: bool = False, city_port: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        if node_id > 0:
            reload_logging_config_node(f"general{node_id}.txt")
            logging.info(f"General {node_id} is running...")
        else:
            reload_logging_config_node(f"supreme_general.txt")
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
