"""Push notification generation service using Azure OpenAI."""

import os
import logging
from typing import Optional, Dict, Any
from openai import AzureOpenAI
from dotenv import load_dotenv

from src.models.client import ClientRecommendation

load_dotenv()

logger = logging.getLogger(__name__)

class NotificationGenerator:
    """Generate personalized push notifications using GPT-4."""

    def __init__(self):
        self.client = None
        self._initialize_azure_client()

    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client."""
        try:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

            if not endpoint or not api_key:
                logger.warning("Azure OpenAI credentials not configured. Notification generation will use templates.")
                return

            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )

            logger.info("Azure OpenAI client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None

    def generate_push_notification(self, recommendation: ClientRecommendation,
                                 client_data: Dict[str, Any]) -> str:
        """Generate personalized push notification."""

        if self.client:
            return self._generate_with_gpt(recommendation, client_data)
        else:
            return self._generate_with_template(recommendation, client_data)

    def _generate_with_gpt(self, recommendation: ClientRecommendation,
                          client_data: Dict[str, Any]) -> str:
        """Generate notification using GPT-4."""
        try:
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

            # Prepare context for GPT
            context = self._prepare_context(recommendation, client_data)

            prompt = f"""
Сгенерируй персональное пуш-уведомление для банковского клиента на основе его данных.

КОНТЕКСТ КЛИЕНТА:
{context}

РЕКОМЕНДУЕМЫЙ ПРОДУКТ: {recommendation.product_name}
ПОТЕНЦИАЛЬНАЯ ВЫГОДА: {recommendation.potential_benefit:,.0f} ₸ в год
ПРИЧИНА РЕКОМЕНДАЦИИ: {recommendation.recommendation_reason}

ТРЕБОВАНИЯ К ТОНУ (TOV):
- На равных, просто и по-человечески
- Обращение на "вы" с маленькой буквы
- Важное — в начало, без воды
- Лёгкий, ненавязчивый тон
- Максимум 1 эмодзи по смыслу
- Длина 180-220 символов

ФОРМАТ ЧИСЕЛ:
- Дробная часть — запятая
- Разряды — пробелы (например: 27 400 ₸)

СТРУКТУРА СООБЩЕНИЯ:
1. Персональное наблюдение по тратам/поведению
2. Конкретная польза продукта
3. Призыв к действию

Сгенерируй ТОЛЬКО текст уведомления без дополнительных комментариев.
"""

            response = self.client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "Ты — эксперт по написанию персональных банковских уведомлений в дружелюбном тоне."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            notification = response.choices[0].message.content.strip()

            # Validate length
            if len(notification) > 250:
                notification = notification[:247] + "..."

            return notification

        except Exception as e:
            logger.error(f"Error generating notification with GPT: {e}")
            return self._generate_with_template(recommendation, client_data)

    def _generate_with_template(self, recommendation: ClientRecommendation,
                               client_data: Dict[str, Any]) -> str:
        """Generate notification using predefined templates."""

        name = recommendation.client_name
        product = recommendation.product_name
        benefit = recommendation.potential_benefit

        # Template-based generation based on product type
        if product == "Карта для путешествий":
            travel_spending = client_data.get('travel_spending_3m', 0)
            return f"{name}, за 3 месяца вы потратили {travel_spending:,.0f} ₸ на поездки и такси. С картой для путешествий вернули бы {benefit/4:,.0f} ₸ кешбэком. Оформить карту"

        elif product == "Премиальная карта":
            balance = client_data.get('avg_monthly_balance_kzt', 0)
            if balance > 1000000:
                return f"{name}, у вас стабильно высокий остаток на счёте. Премиальная карта даст повышенный кешбэк и бесплатные снятия. Экономия {benefit:,.0f} ₸/год. Подключить"
            else:
                return f"{name}, ваши траты в ресторанах и на покупках дают право на премиальную карту с повышенным кешбэком. Потенциальная выгода {benefit:,.0f} ₸/год. Оформить"

        elif product == "Кредитная карта":
            top_categories = client_data.get('top_categories', ['покупки'])
            cat1, cat2 = (top_categories[:2] + ['', ''])[:2]
            categories_str = f"{cat1}, {cat2}".rstrip(', ')
            return f"{name}, ваши топ-категории — {categories_str}. Кредитная карта даст до 10% кешбэк. Выгода {benefit:,.0f} ₸/год. Оформить карту"

        elif product == "Обмен валют":
            fx_volume = client_data.get('fx_volume_3m', 0)
            return f"{name}, вы активно работаете с валютой (оборот {fx_volume:,.0f} ₸). Выгодный обмен в приложении сэкономит {benefit:,.0f} ₸/год. Настроить обмен"

        elif product == "Кредит наличными":
            return f"{name}, если нужны средства на крупные расходы — кредит наличными с гибкими условиями. Экономия на процентах {benefit:,.0f} ₸/год. Узнать лимит"

        elif "Депозит" in product:
            if "Сберегательный" in product:
                rate = "16,5%"
            elif "Накопительный" in product:
                rate = "15,5%"
            else:
                rate = "14,5%"

            return f"{name}, у вас есть свободные средства. Размещение на депозите {rate} годовых принесёт {benefit:,.0f} ₸ дохода. Открыть вклад"

        elif product == "Инвестиции":
            return f"{name}, попробуйте инвестиции с низким порогом входа и без комиссий на старт. Потенциальная экономия {benefit:,.0f} ₸/год. Открыть счёт"

        elif product == "Золотые слитки":
            return f"{name}, для диверсификации портфеля рассмотрите золотые слитки. Защита от инфляции на сумму {benefit:,.0f} ₸/год. Узнать подробнее"

        else:
            return f"{name}, рекомендуем {product} с потенциальной выгодой {benefit:,.0f} ₸ в год. Узнать условия"

    def _prepare_context(self, recommendation: ClientRecommendation,
                        client_data: Dict[str, Any]) -> str:
        """Prepare client context for GPT prompt."""

        context_parts = [
            f"Имя: {recommendation.client_name}",
            f"Текущий продукт: {recommendation.current_product or 'Не указан'}",
        ]

        # Add relevant behavioral data
        if 'avg_monthly_balance_kzt' in client_data:
            balance = client_data['avg_monthly_balance_kzt']
            context_parts.append(f"Средний остаток: {balance:,.0f} ₸")

        if 'total_spending_3m' in client_data:
            spending = client_data['total_spending_3m']
            context_parts.append(f"Траты за 3 мес: {spending:,.0f} ₸")

        if 'top_categories' in client_data:
            categories = client_data['top_categories'][:3]
            context_parts.append(f"Топ-категории: {', '.join(categories)}")

        if 'travel_spending_3m' in client_data and client_data['travel_spending_3m'] > 0:
            travel = client_data['travel_spending_3m']
            context_parts.append(f"Траты на поездки: {travel:,.0f} ₸")

        if 'fx_activity_score' in client_data and client_data['fx_activity_score'] > 0:
            context_parts.append(f"Валютная активность: высокая")

        return "\n".join(context_parts)

    def generate_for_all_recommendations(self) -> Dict[int, str]:
        """Generate notifications for all client recommendations."""
        from src.utils.database import db_manager
        from sqlalchemy import text

        session = db_manager.get_session()
        notifications = {}

        try:
            # Get all top recommendations with client data
            result = session.execute(text("""
                SELECT c.client_code, c.name, p.name as product_name,
                       cr.potential_benefit, cr.recommendation_reason,
                       c.avg_monthly_balance_kzt
                FROM client_recommendations cr
                JOIN clients c ON cr.client_code = c.client_code
                JOIN products p ON cr.product_id = p.id
                WHERE cr.rank = 1
                ORDER BY c.client_code
            """)).fetchall()

            for row in result:
                recommendation = ClientRecommendation(
                    client_code=row.client_code,
                    client_name=row.name,
                    current_product=None,
                    rank=1,
                    product_name=row.product_name,
                    potential_benefit=row.potential_benefit,
                    recommendation_reason=row.recommendation_reason,
                    confidence_score=0.8
                )

                client_data = {
                    'avg_monthly_balance_kzt': float(row.avg_monthly_balance_kzt)
                }

                notification = self.generate_push_notification(recommendation, client_data)
                notifications[row.client_code] = notification

            logger.info(f"Generated {len(notifications)} push notifications")

        except Exception as e:
            logger.error(f"Error generating notifications: {e}")

        finally:
            session.close()

        return notifications