from app.routers.prompts import load_prompts, load_injections


def test_prompts_load_and_have_required_fields():
    prompts = load_prompts()
    assert len(prompts) > 0
    for p in prompts:
        assert "id" in p and "category" in p and "prompt" in p and "tolerance" in p


def test_prompt_ids_are_unique():
    prompts = load_prompts()
    ids = [p["id"] for p in prompts]
    assert len(ids) == len(set(ids))


def test_injections_load_and_have_required_fields():
    attacks = load_injections()
    assert len(attacks) > 0
    for a in attacks:
        assert "id" in a and "category" in a and "attack" in a
