import pytest
from number_converter_whitebox import convert_to_polish_name


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        pytest.param(0, "zero", id="TC01"),
        pytest.param(1, "jeden", id="TC02"),
        pytest.param(
            999998,
            "dziewięćset dziewięćdziesiąt dziewięć tysięcy dziewięćset dziewięćdziesiąt osiem",
            id="TC03",
        ),
        pytest.param(
            999999,
            "dziewięćset dziewięćdziesiąt dziewięć tysięcy dziewięćset dziewięćdziesiąt dziewięć",
            id="TC04",
        ),
        pytest.param(10, "dziesięć", id="TC05"),
        pytest.param(11, "jedenaście", id="TC06"),
        pytest.param(12, "dwanaście", id="TC07"),
        pytest.param(19, "dziewiętnaście", id="TC08"),
        pytest.param(20, "dwadzieścia", id="TC09"),
        pytest.param(21, "dwadzieścia jeden", id="TC10"),
        pytest.param(99, "dziewięćdziesiąt dziewięć", id="TC11"),
        pytest.param(100, "sto", id="TC12"),
        pytest.param(101, "sto jeden", id="TC13"),
        pytest.param(110, "sto dziesięć", id="TC14"),
        pytest.param(111, "sto jedenaście", id="TC15"),
        pytest.param(120, "sto dwadzieścia", id="TC16"),
        pytest.param(200, "dwieście", id="TC17"),
        pytest.param(505, "pięćset pięć", id="TC18"),
        pytest.param(999, "dziewięćset dziewięćdziesiąt dziewięć", id="TC19"),
        pytest.param(1000, "tysiąc", id="TC20"),
        pytest.param(1001, "tysiąc jeden", id="TC21"),
        pytest.param(1010, "tysiąc dziesięć", id="TC22"),
        pytest.param(1100, "tysiąc sto", id="TC23"),
        pytest.param(1111, "tysiąc sto jedenaście", id="TC24"),
        pytest.param(2000, "dwa tysiące", id="TC25"),
        pytest.param(5000, "pięć tysięcy", id="TC26"),
        pytest.param(10000, "dziesięć tysięcy", id="TC27"),
        pytest.param(10010, "dziesięć tysięcy dziesięć", id="TC28"),
        pytest.param(10101, "dziesięć tysięcy sto jeden", id="TC29"),
        pytest.param(12000, "dwanaście tysięcy", id="TC30"),
        pytest.param(21000, "dwadzieścia jeden tysięcy", id="TC31"),
        pytest.param(22000, "dwadzieścia dwa tysiące", id="TC32"),
        pytest.param(101000, "sto jeden tysięcy", id="TC33"),
        pytest.param(112000, "sto dwanaście tysięcy", id="TC34"),
        pytest.param(122000, "sto dwadzieścia dwa tysiące", id="TC35"),
        pytest.param(205020, "dwieście pięć tysięcy dwadzieścia", id="TC36"),
        pytest.param(
            123456,
            "sto dwadzieścia trzy tysiące czterysta pięćdziesiąt sześć",
            id="TC37",
        ),
    ],
)
def test_convert_to_polish_name_valid(number: int, expected: str) -> None:
    result = convert_to_polish_name(number)
    assert result == expected
    assert isinstance(result, str)


@pytest.mark.parametrize(
    "number",
    [
        pytest.param(-1, id="TC38"),
        pytest.param(1000000, id="TC39"),
        pytest.param(1.5, id="TC40"),
        pytest.param("123", id="TC41"),
        pytest.param(None, id="TC42"),
    ],
)
def test_convert_to_polish_name_invalid(number) -> None:
    e = ValueError if isinstance(number, int) else TypeError
    with pytest.raises(e):
        convert_to_polish_name(number)
