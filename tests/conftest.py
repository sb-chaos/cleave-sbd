import pytest
import fracture


@pytest.fixture()
def default_en_no_clean_no_span_fixture():
    en_segmenter = fracture.Segmenter(language="en", clean=False, char_span=False)
    return en_segmenter


@pytest.fixture()
def en_with_clean_no_span_fixture():
    en_segmenter = fracture.Segmenter(language="en", clean=True, char_span=False)
    return en_segmenter


@pytest.fixture()
def en_no_clean_with_span_fixture():
    en_segmenter = fracture.Segmenter(language="en", clean=False, char_span=True)
    return en_segmenter


@pytest.fixture()
def hi_default_fixture():
    hi_segmenter = fracture.Segmenter(language="hi", clean=False, char_span=False)
    return hi_segmenter


@pytest.fixture()
def mr_default_fixture():
    mr_segmenter = fracture.Segmenter(language="mr", clean=False, char_span=False)
    return mr_segmenter


@pytest.fixture()
def zh_default_fixture():
    zh_segmenter = fracture.Segmenter(language="zh", clean=False, char_span=False)
    return zh_segmenter


@pytest.fixture()
def es_default_fixture():
    es_segmenter = fracture.Segmenter(language="es", clean=False, char_span=False)
    return es_segmenter


@pytest.fixture()
def es_with_clean_no_span_fixture():
    es_segmenter_clean = fracture.Segmenter(language="es", clean=True, char_span=False)
    return es_segmenter_clean


@pytest.fixture()
def am_default_fixture():
    am_segmenter = fracture.Segmenter(language="am", clean=False, char_span=False)
    return am_segmenter


@pytest.fixture()
def ar_default_fixture():
    ar_segmenter = fracture.Segmenter(language="ar", clean=False, char_span=False)
    return ar_segmenter


@pytest.fixture()
def hy_default_fixture():
    hy_segmenter = fracture.Segmenter(language="hy", clean=False, char_span=False)
    return hy_segmenter


@pytest.fixture()
def bg_default_fixture():
    bg_segmenter = fracture.Segmenter(language="bg", clean=False, char_span=False)
    return bg_segmenter


@pytest.fixture()
def ur_default_fixture():
    ur_segmenter = fracture.Segmenter(language="ur", clean=False, char_span=False)
    return ur_segmenter


@pytest.fixture()
def ru_default_fixture():
    ru_segmenter = fracture.Segmenter(language="ru", clean=False, char_span=False)
    return ru_segmenter


@pytest.fixture()
def pl_default_fixture():
    pl_segmenter = fracture.Segmenter(language="pl", clean=False, char_span=False)
    return pl_segmenter


@pytest.fixture()
def fa_default_fixture():
    fa_segmenter = fracture.Segmenter(language="fa", clean=False, char_span=False)
    return fa_segmenter


@pytest.fixture()
def nl_default_fixture():
    nl_segmenter = fracture.Segmenter(language="nl", clean=False, char_span=False)
    return nl_segmenter


@pytest.fixture()
def da_default_fixture():
    da_segmenter = fracture.Segmenter(language="da", clean=False, char_span=False)
    return da_segmenter


@pytest.fixture()
def da_with_clean_no_span_fixture():
    da_segmenter = fracture.Segmenter(language="da", clean=True, char_span=False)
    return da_segmenter


@pytest.fixture()
def fr_default_fixture():
    fr_segmenter = fracture.Segmenter(language="fr", clean=False, char_span=False)
    return fr_segmenter


@pytest.fixture()
def my_default_fixture():
    my_segmenter = fracture.Segmenter(language="my", clean=False, char_span=False)
    return my_segmenter


@pytest.fixture()
def el_default_fixture():
    el_segmenter = fracture.Segmenter(language="el", clean=False, char_span=False)
    return el_segmenter


@pytest.fixture()
def it_default_fixture():
    it_segmenter = fracture.Segmenter(language="it", clean=False, char_span=False)
    return it_segmenter


@pytest.fixture()
def ja_default_fixture():
    ja_segmenter = fracture.Segmenter(language="ja", clean=False, char_span=False)
    return ja_segmenter


@pytest.fixture()
def ja_with_clean_no_span_fixture():
    ja_segmenter = fracture.Segmenter(language="ja", clean=True, char_span=False)
    return ja_segmenter


@pytest.fixture()
def de_default_fixture():
    de_segmenter = fracture.Segmenter(language="de", clean=False, char_span=False)
    return de_segmenter


@pytest.fixture()
def de_with_clean_no_span_fixture():
    de_segmenter = fracture.Segmenter(language="de", clean=True, char_span=False)
    return de_segmenter


@pytest.fixture()
def kk_default_fixture():
    kk_segmenter = fracture.Segmenter(language="kk", clean=False, char_span=False)
    return kk_segmenter


@pytest.fixture()
def sk_default_fixture():
    sk_segmenter = fracture.Segmenter(language="sk", clean=False, char_span=False)
    return sk_segmenter
