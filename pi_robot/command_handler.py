def command_handler(
    button_x,
    button_y,
    button_a,
    button_b,
    mouth,
    ears,
    eyes,
    eyebrows,
) -> None:

    print(f"Button X: {button_x.is_pressed}")
    print(f"Button Y: {button_y.is_pressed}")
    print(f"Button A: {button_a.is_pressed}")
    print(f"Button B: {button_b.is_pressed}")

    if button_x.is_pressed:
        mouth.animate(1.0)
    if button_y.is_pressed:
        ears.wiggle()
    if button_a.is_pressed:
        eyes.blink()
    if button_b.is_pressed:
        eyebrows.wiggle()
