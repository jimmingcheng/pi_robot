from pi_robot.moving_body_part import MovingBodyPart


class Eyebrows(MovingBodyPart):
    def relax(self) -> None:
        if not self.left_servo or not self.right_servo:
            return

        self.left_servo.angle = 90
        self.right_servo.angle = 90

    def lower_left(self) -> None:
        if not self.left_servo:
            return

        self.left_servo.angle = 45

    def lower_right(self) -> None:
        if not self.right_servo:
            return

        self.right_servo.angle = 135

    def raise_left(self) -> None:
        if not self.left_servo:
            return

        self.left_servo.angle = 135

    def raise_right(self) -> None:
        if not self.right_servo:
            return

        self.right_servo.angle = 45
