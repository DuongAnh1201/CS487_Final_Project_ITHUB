"""Imports every ORM model so ``Base.metadata`` knows all tables (Alembic and create_all use it)."""

from app.modules.ast import models as ast_models
from app.modules.cls import models as cls_models
from app.modules.iss import models as iss_models
from app.modules.ntf import models as ntf_models
from app.modules.ord import models as ord_models
from app.modules.prj import models as prj_models
from app.modules.rpt import models as rpt_models
from app.modules.usr import models as usr_models
from app.shared import audit

MODEL_MODULES = (ast_models, cls_models, iss_models, ntf_models, ord_models, prj_models, rpt_models, usr_models, audit)
