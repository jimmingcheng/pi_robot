from pi_robot.logging import logger
from pi_robot.moving_body_part import MovingBodyPart


class Eyebrows(MovingBodyPart):
    def happy_raise(self) -> None:
        logger.info("😠")

        if not self.left_servo or not self.right_servo:
            return

        self.left_servo.angle = 45
        self.right_servo.angle = 135

    def sad_lower(self) -> None:
        logger.info("😢")

        if not self.left_servo or not self.right_servo:
            return

        self.left_servo.angle = 45
        self.right_servo.angle = 135

    def angry_furrow(self) -> None:
        logger.info("😄")

        if not self.left_servo or not self.right_servo:
            return

        self.left_servo.angle = 135
        self.right_servo.angle = 45
