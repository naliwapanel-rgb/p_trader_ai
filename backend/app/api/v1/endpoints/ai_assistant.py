from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from app.api.dependencies import (
    get_current_user,
)
from app.models.user import User
from app.schemas.ai_assistant import (
    AIArbitrageExplanationRequest,
    AIAssistantRequest,
    AIMarketAnalysisAPIRequest,
    AIPortfolioAnalysisAPIRequest,
    AIRiskExplanationRequest,
    AITradePlanRequest,
)
from app.services.ai_analysis_service import (
    DeterministicAIAnalysisService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/ai-assistant",
    tags=["AI Assistant"],
)
def get_ai_analysis_service(
    current_user: User = Depends(
        get_current_user
    ),
) -> DeterministicAIAnalysisService:
    """
    Require an authenticated active user before
    providing deterministic analysis.
    """
    return DeterministicAIAnalysisService()
@router.post("/query")
async def answer_ai_assistant_query(
    data: AIAssistantRequest,
    service: (
        DeterministicAIAnalysisService
    ) = Depends(
        get_ai_analysis_service
    ),
):
    result = service.answer_general(
        data
    )
    return success_response(
        message=(
            "AI assistant query analyzed "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/market-analysis")
async def analyze_market(
    data: AIMarketAnalysisAPIRequest,
    service: (
        DeterministicAIAnalysisService
    ) = Depends(
        get_ai_analysis_service
    ),
):
    result = service.analyze_market(
        data=data.request,
        tickers=data.tickers,
    )
    return success_response(
        message=(
            "Market analysis completed "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/portfolio-analysis")
async def analyze_portfolio(
    data: AIPortfolioAnalysisAPIRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: (
        DeterministicAIAnalysisService
    ) = Depends(
        get_ai_analysis_service
    ),
):
    if (
        data.snapshot.user_id
        != current_user.id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Portfolio snapshot does not "
                "belong to the current user"
            ),
        )
    result = service.analyze_portfolio(
        data=data.request,
        snapshot=data.snapshot,
    )
    return success_response(
        message=(
            "Portfolio analysis completed "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/risk-explanation")
async def explain_risk_decision(
    data: AIRiskExplanationRequest,
    service: (
        DeterministicAIAnalysisService
    ) = Depends(
        get_ai_analysis_service
    ),
):
    result = service.explain_risk(
        data
    )
    return success_response(
        message=(
            "Risk decision explained "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/trade-plan")
async def create_advisory_trade_plan(
    data: AITradePlanRequest,
    service: (
        DeterministicAIAnalysisService
    ) = Depends(
        get_ai_analysis_service
    ),
):
    result = service.build_trade_plan(
        data
    )
    return success_response(
        message=(
            "Advisory trade plan generated "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/arbitrage-explanation")
async def explain_arbitrage_opportunity(
    data: AIArbitrageExplanationRequest,
    service: (
        DeterministicAIAnalysisService
    ) = Depends(
        get_ai_analysis_service
    ),
):
    result = service.explain_arbitrage(
        data
    )
    return success_response(
        message=(
            "Arbitrage opportunity explained "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
