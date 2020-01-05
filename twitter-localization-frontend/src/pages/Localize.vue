<template>
    <div class="row">
      <div class="col-md-12">
        <card>
          <h4 class="card-title">Localize User</h4>
          <label>
            Twitter Handle: @
            <input v-model="queryScreenName" type="text">
          </label>
          <label style="margin-left: 15px">
            Meta-Model:
            <select v-model="selectedMetamodel">
              <option v-for="metamodel in availableMetamodels"
                      :value="metamodel">
                {{ metamodel }}
              </option>
            </select>
          </label>
          <p-button
            style="margin-left: 15px"
            @click.native="localize()">
            <i class="ti-pin icon-padded"></i>Localize
          </p-button>
        </card>
        <card>
          <template slot="header">
            <h4 class="card-title">Results</h4>
            <table class="table table-hover">
              <thead>
                <th>Twitter Handle</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Meta-Model</th>
              </thead>
              <tbody>
              <tr v-for="result in localizations.pending">
                <td>@{{ result.screenName }}</td>
                <td>pending...</td>
              </tr>
              <tr v-for="result in localizations.complete">
                <td><a target="_blank" v-bind:href="`https://twitter.com/${result.screenName}`">@{{ result.screenName }}</a></td>
                <td>{{ result.isSwiss === "true" ? "swiss" : "foreign" }}</td>
                <td>{{ result.confidence }}</td>
                <td>{{ result.metamodelName }}</td>
              </tr>
              <tr v-for="result in localizations.failed">
                <td class="localization-entry-failed">@{{ result.screenName }}</td>
                <td class="localization-entry-failed">failed</td>
                <td class="localization-entry-failed"></td>
                <td class="localization-entry-failed">{{ result.metamodelName }}</td>
              </tr>
              </tbody>
            </table>
          </template>
        </card>
      </div>

    </div>
</template>


<script>
  import $ from 'jquery';
  import { context } from '../assets/js/context'
  import { eventBus } from "../assets/js/EventBus";

  export default {
      data: function(){
          return {
              availableMetamodels: [],
              metamodelIsAvailable: false,
              queryScreenName: "",
              selectedMetamodel: "",
              localizations: [],
              results: []
          }
      },
      mounted: function() {
          eventBus.$on("metamodelsUpdated", () => {
              const available = context.availableMetamodels();
              if(available.length > 0) {
                  this.metamodelIsAvailable = true;
                  this.availableMetamodels = available;
                  if (this.selectedMetamodel === "") {
                      this.selectedMetamodel = available[0];
                  }
              } else {
                  this.metamodelIsAvailable = false;
                  this.availableMetamodels = ["All metamodels offline"];
                  this.selectedMetamodel = "";
              }
          });
          eventBus.$on("localizationsUpdated", () => {
            this.localizations = context.localizations;
          });
      },
      methods: {
          localize: function () {
              const pendingUserPlaceholder = {
                "screenName": this.queryScreenName,
                "metamodelName": this.selectedMetamodel
              };
              this.localizations.pending.push(pendingUserPlaceholder);
              context.localizeUser(this.queryScreenName, this.selectedMetamodel);
          }
      }
  };
</script>


<style>
  td.localization-entry-failed {
    color: red;
  }
</style>
