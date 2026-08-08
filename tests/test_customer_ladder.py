from customer_ladder.models import CustomerIntake, OfferTier
from customer_ladder.service import build_blueprint


def test_small_scope_stays_diy():
    result = build_blueprint(CustomerIntake(goal="Organize one small idea set", asset_count=8))
    assert result.recommended_tier == OfferTier.DIY


def test_real_source_set_routes_to_starter():
    result = build_blueprint(
        CustomerIntake(
            goal="Recover a product direction",
            source_locations=["Google Drive"],
            asset_count=60,
            recurring_themes=["knowledge recovery"],
        )
    )
    assert result.recommended_tier == OfferTier.STARTER


def test_multiple_opportunities_route_to_growth():
    result = build_blueprint(
        CustomerIntake(
            goal="Turn recovered knowledge into products",
            asset_count=120,
            opportunities=["course", "audit service"],
        )
    )
    assert result.recommended_tier == OfferTier.GROWTH


def test_governance_routes_to_enterprise():
    result = build_blueprint(
        CustomerIntake(goal="Build governed team knowledge", team_size=4, needs_governance=True)
    )
    assert result.recommended_tier == OfferTier.ENTERPRISE
