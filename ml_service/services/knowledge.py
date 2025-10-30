import logging
import time


logger = logging.getLogger("ml_service")

class Knowledge():
    def __init__(self, mode=None, type="similar", scope=[], kb_location=None, kb_db=None, kb_task_type=None, parameters=None,confidence=None, uuid=None,
                prediction=False, prediction_error=None, identity=[1], skill_class=None, skill_instance=None, source=[], expected_cost=None, time=time.time(), datetime=time.ctime(),
                tags=[], equal_start=False, equal_tags=[], cost_function=[],identification_name="",time_range=(0,float('inf')), similarity=None):
        self.mode = mode  # either None, "specific", "local", "global"     (if "None", but parameters is not empty, the parameters will be used as centroid)
        self.type = type  # also possible: "predicted" (use prediction), "all" (gives list of knowledges, no predicted ones),
        self.scope = scope  # scope (tags of results to make this knowledge)
        self.kb_location = kb_location  # location of the knowledge base
        self.kb_db = kb_db  # needed if type is specific
        self.kb_task_type = kb_task_type  # needed if type is specific
        self.parameters = parameters #dict() with unnormalised Theta
        self.confidence = confidence
        self.uuid = uuid   # single uuid or list of uuids
        self.prediction = prediction  # bool, wether this knowledge was predicted or not
        self.prediction_error = prediction_error
        self.identity = identity  # task identity
        self.skill_class = skill_class  # eg. "insertion"
        self.skill_instance = skill_instance  #  skill_instance from problem_definition
        self.source = source  # uuid(s) of the source ml_results
        self.expected_cost = expected_cost
        self.time = time  # time when knowledge point was created (time.time())
        self.datetime = datetime  # time.ctime()
        self.tags = tags  #actual tags of the knowledge itself
        self.equal_start = equal_start  # if True the svm.py will use the same first batch (from equal_tags) every time
        self.equal_tags = equal_tags
        self.cost_function = cost_function
        self.identification_name = identification_name  # identification string, because uuid is random
        self.time_range = time_range  # time window from which knowledge can be collected to create new knowledge points
        self.similarity = similarity  # list of objects with request probabilities

    def update(self):
        self.identification_name = self.get_identification_name()

    def get_identification_name(self):
        return str(self.skill_class)+str(self.skill_instance)+str(self.identity)+", ".join(self.tags)
        #return str({"skill_class": self.skill_class, "tags": self.tags, "identity": self.identity,"skill_instance":self.skill_instance})   # exactly the same as for problem_definition

    def to_dict(self) -> dict:
        meta_information = {
            "mode": self.mode,
            "type": self.type,
            "scope": self.scope,
            "kb_location": self.kb_location,
            "confidence": self.confidence,
            "uuid": self.uuid,
            "prediction": self.prediction,
            "prediction_error": self.prediction_error,
            "identity": self.identity,
            "skill_class": self.skill_class,
            "source": self.source,
            "expected_cost": self.expected_cost,
            "time": self.time,
            "datetime":self.datetime,
            "tags": self.tags,
            "equal_start": self.equal_start,
            "equal_tags": self.equal_tags,
            "cost_function": self.cost_function,
            "kb_db": self.kb_db,
            "kb_task_type": self.kb_task_type,
            "skill_instance": self.skill_instance,
            "identification_name": self.identification_name,
            "time_range":self.time_range,
            "similarity":self.similarity
        }
        knowledge_dict = {
            "parameters": self.parameters,
            "meta": meta_information
        }
        return knowledge_dict
    
    def from_dict(self, input: dict):
        self.parameters = input.get("parameters", None)
        if "meta" in input:
            input = input["meta"]

        self.mode = input.get("mode", None)
        self.type = input.get("type", "similar")
        self.scope = input.get("scope", [])
        self.kb_location = input.get("kb_location", None)
        self.confidence = input.get("confidence", None)
        self.uuid = input.get("uuid", None)
        self.prediction = input.get("prediction", False)
        self.prediction_error = input.get("prediction_error", False)
        self.identity = input.get("identity", [1])
        self.skill_class = input.get("skill_class", None)
        self.source = input.get("source", [])
        self.expected_cost = input.get("expected_cost", None)
        self.time = input.get("time", None)
        self.datetime = input.get("datetime", None)
        self.tags = input.get("tags", [])
        self.tags.extend(input.get("kb_tags", []))  # dont use kb_tags anymore
        self.equal_tags = input.get("equal_tags", [])
        self.equal_start = input.get("equal_start", False)
        self.cost_function = input.get("cost_function", [])
        self.kb_db = input.get("kb_db", None)
        self.kb_task_type = input.get("kb_task_type", None)
        self.skill_instance = input.get("skill_instance", None)
        self.time_range = input.get("time_range",(0,float('inf')))
        self.similarity = input.get("similarity",None)
        self.update()
    
    def get_db_format(self):
        db_format = dict()
        db_format["parameters"] = self.parameters
        meta_info = dict()
        meta_info["time"] = self.time
        meta_info["mode"] = self.mode
        meta_info["scope"] = self.scope
        meta_info["source"] = self.source
        meta_info["expected_cost"] = self.expected_cost
        meta_info["confidence"] = self.confidence
        meta_info["prediction"] = self.prediction
        meta_info["prediction_error"] = self.prediction_error
        meta_info["identity"] = self.identity
        meta_info["tags"] = self.tags
        meta_info["cost_function"] = self.cost_function
        meta_info["skill_instance"] = self.skill_instance
        meta_info["identification_name"] = self.identification_name
        meta_info["time_range"] = self.time_range
        meta_info["similarity"] = self.similarity
        db_format["meta"] = meta_info
        return db_format
        


    def check_consistency(self):
        if self.mode == "global":
            if type(self.kb_location) != str:
                logger.error("knowledge mode is \""+self.mode+"\" but no kb_location was set.")
        if self.mode == "global" or self.mode == "local":
            if self.type is None:
                logger.error("knowledge mode is \""+self.mode+"\" but knowledge type was not set. Default is local")
        if (self.equal_start and (type(self.kb_location) != str)) or (self.equal_start and not self.equal_tags):
            logger.error("All agents should start with the same batch (equal start is True), but no location or tags are specified")





