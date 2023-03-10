import logging
import threading

from node_socket import UdpSocket


class City:

    def __init__(self, my_port: int, number_general: int) -> None:
        self.number_general = number_general
        self.my_port = my_port
        self.node_socket = UdpSocket(my_port)

    def start(self):
        """
        TODO
        :return: string
        """
        logging.info(f"Listen to incoming messages...")
        orders = []
        for i in range(self.number_general):
            msg, _ = self.node_socket.listen()
            msg = msg.split('~')
            sender, order = msg[0], int(msg[1].split('=')[-1])

            orders.append(order)

            if order:
                order = "ATTACK"
            else:
                order = "RETREAT from"
            logging.info(f"{sender} {order} us!")

        logging.info(f"Concluding what happen...")
        if len(orders) < 2:
            logging.info(f"GENERAL CONSENSUS: ERROR_LESS_THAN_TWO_GENERALS")
            logging.shutdown()
            return "ERROR_LESS_THAN_TWO_GENERALS"
        else:
            if sum(orders) == 3:
                logging.info(f"GENERAL CONSENSUS: ATTACK")
                logging.shutdown()
                return "ATTACK"
            elif sum(orders) == 2 or sum(orders) == 1:
                logging.info(f"GENERAL CONSENSUS: FAILED")
                logging.shutdown()
                return "FAILED"
            else:
                logging.info(f"GENERAL CONSENSUS: RETREAT")
                logging.shutdown()
                return "RETREAT"


def thread_exception_handler(args):
    logging.error(f"Uncaught exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def main(city_port: int, number_general: int):
    threading.excepthook = thread_exception_handler
    try:
        logging.debug(f"city_port: {city_port}")
        logging.info(f"City is running...")
        logging.info(f"Number of loyal general: {number_general}")
        city = City(my_port=city_port, number_general=number_general)
        return city.start()

    except Exception:
        logging.exception("Caught Error")
        raise
