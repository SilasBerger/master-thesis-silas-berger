import $ from 'jquery';
import { eventBus } from "./EventBus";

class Context {

  constructor() {
    this.apiServer = "http://127.0.0.1:5000";
    this.metamodelStatus = {};
    this.localizations = {
      complete: [],
      pending: [],
      failed: []
    };
    this.statistics = null;
    this._updateMetamodelStatus();

    setInterval(
      (function(self) {
        return function() {
          self._updateMetamodelStatus();
          self._updateLocalizations();
        }
      })(this), 1000);
  }

  _updateMetamodelStatus() {
    $.get(`${this.apiServer}/metamodels`, (res, status) => {
      this.metamodelStatus = res;
      eventBus.$emit("metamodelsUpdated");
    });
  }

  _updateLocalizations() {
    $.get(`${context.apiServer}/localizations`, (res, status) => {
      this.localizations.complete = res.complete;
      this.localizations.pending = res.pending;
      this.localizations.failed = res.failed;
      eventBus.$emit("localizationsUpdated");
    });
  }

  buildMetamodel(metamodelName) {
    $.ajax({
      type: 'post',
      url: `${this.apiServer}/buildmetamodel`,
      data: JSON.stringify({"metamodel": metamodelName}),
      contentType: 'application/json',
      headers: {
      },
      success: function (data) {

      },
      error: function (err) {
        console.error("Unable to build metamodel " + metamodelName + ": " + err);
      }
    })
  }

  localizeUser(screenName, metamodelName) {
    const requestData = {
      "screenName": screenName,
      "metamodel": metamodelName
    };
    $.ajax({
      type: 'post',
      url: `${this.apiServer}/localize`,
      data: JSON.stringify(requestData),
      contentType: 'application/json',
      headers: {
      },
      success: function (data) {

      },
      error: function (err) {
        console.error("Unable to localize user " + screenName + ": " + err);
      }
    })
  }

  getStatistics() {
    if (this.statistics == null) {
      $.get(`${this.apiServer}/statistics`, (res, status) => {
        this.statistics = res;
        eventBus.$emit("statisticsLoaded");
      });
    }
    // This can be null if lazy-loaded (listen for event if needed)
    return this.statistics
  }

  allMetamodels() {
    return Object.keys(this.metamodelStatus);
  }

  listMetamodels() {
    const metamodels = [];
    Object.keys(this.metamodelStatus).forEach(key => {
      metamodels.push(this.metamodelStatus[key]);
    });
    return metamodels;
  }

  availableMetamodels() {
    const result = [];
    Object.keys(this.metamodelStatus).forEach(key => {
      if(this.metamodelStatus[key]["status"] === "online") {
        result.push(key)
      }
    });
    return result;
  }
}

export const context = new Context();
